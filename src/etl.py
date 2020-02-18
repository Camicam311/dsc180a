from urllib.request import urlretrieve
from zipfile import ZipFile, BadZipfile
from lxml import etree
from copy import deepcopy
from py7zr import unpack_7zarchive
import shutil
import sys
import os
import pandas as pd
from csv import writer

# Paths are as follows
# i.e. Page: page_id, page_title
#       -> Revision: 'rev_id', 'parent_id', 'timestamp',
#                     'comment' ,'model', 'format',
#                     'edit', 'sha1'}
#           -> Contributor: 'username', 'user_id', 'user_ip'
xpath_dict = {'page': 'ns:page',
              'page_id': 'ns:id',
              'page_title': 'ns:title',
              'revision': 'ns:revision',
              'rev_id': 'ns:id',
              'parent_id': 'ns:parentid',
              'timestamp': 'ns:timestamp',
              'model': 'ns:model',
              'format': 'ns:format',
              'edit': 'ns:text',
              'comment': 'ns:comment',
              'contributor': 'ns:contributor',
              'username': 'ns:username',
              'user_id': 'ns:id',
              'user_ip': 'ns:ip',
              }

page_level_tags = {'page_id', 'page_title'}
rev_level_tags = {'rev_id', 'parent_id', 'timestamp',
                    'comment' ,'model', 'format',
                    'edit', 'sha1'}
contr_level_tags = {'username', 'user_id', 'user_ip'}

nsmap = {'ns': 'http://www.mediawiki.org/xml/export-0.10/'}

# ---------------------------------------------------------------------
# Helper Functions for Getting Data
# ---------------------------------------------------------------------

def context_to_txt(context, fp_txt, data_dir, tags,
                    page_chunk=100):
    '''loops through an XML object, and writes page elements per file.'''
    page_num = 1

    # create an empty tree to add XML elements to ('pages')
    tree = etree.ElementTree()
    root = etree.Element("wikimedia")

    # loop through the large XML tree (streaming)
    for event, elem in context:

        # After a given number of pages, write the tree to the XML file
        # and reset the tree / create a new file.
        if page_num % page_chunk == 0:
            tree, root = write_tree_to_txt(
                    tree=tree, root=root, page_num=page_num,
                    fp_txt=fp_txt, data_dir=data_dir, tags=tags
                    )

        # add the 'page' element to the small tree
        root.append(deepcopy(elem))
        page_num += 1

        # release uneeded XML from memory
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
    if page_num % page_chunk:
        write_tree_to_txt(
                tree=tree, root=root, page_num=page_num, fp_txt=fp_txt,
                data_dir=data_dir, tags=tags
                )
    del context

def write_tree_to_txt(tree, root, page_num, fp_txt, data_dir, tags,
                      light_format=True):
    """
    Writes tree to csv file
    :param tree: Etree
    :param root: Root node of tree
    :param page_num: Last page encoded within the tree
    :param fp_txt: File path of the txt file
    :param data_dir: Data directory for output
    :param tags: Tags used for output
    :return:
    """
    if light_format:
        convert_tree_light_format(root=root, fp_txt=fp_txt)
        print('converted up to', page_num)
        return etree.ElementTree(), etree.Element("wikimedia")
    print('begin conversion of', page_num)
    df = convert_tree_to_df(root=root, tags=tags)
    print('converted up to', page_num)
    del tree
    del root
    if not os.path.exists(data_dir + fp_txt):
        df.to_csv(data_dir + fp_txt, index=False)
        print('converted up to',page_num,'to csv')
    else:
        df.to_csv(data_dir + fp_txt, mode='a', index=False, header=False)
        print('appended up to',page_num,'to csv')
    del df
    return etree.ElementTree(), etree.Element("wikimedia")

# Get element text if exists
# Else None
def get_tag_if_exists(parent, tag):
    res = parent.find(xpath_dict[tag], namespaces=nsmap)
    if res != None:
        return res.text
    return res

def convert_tree_light_format(root, fp_txt):
    fh = open(fp_txt, 'a')
    cols = ['timestamp', 'edit', 'username']
    for page_el in root.iterfind(xpath_dict['page'], namespaces=nsmap):
        page_title = get_tag_if_exists(page_el, 'page_title')
        fh.write(page_title + '\n')
        
        time_mapper = {}
        for rev_el in page_el.iterfind(xpath_dict['revision'],
                                       namespaces=nsmap):
            timestamp = get_tag_if_exists(rev_el, cols[0])
            curr_rev = get_tag_if_exists(rev_el, cols[1])
            contr_el = rev_el.find(xpath_dict['contributor'], namespaces=nsmap)
            user = get_tag_if_exists(contr_el, cols[2])
            if not user:
                user = get_tag_if_exists(contr_el, 'user_ip')
            if user:
                user = user.replace(' ', '_')
            curr_line = (curr_rev, user)
            time_mapper[timestamp] = curr_line
            
        rev_mapper = {}
        rev_count = 1
        lines = []
        for time in sorted(time_mapper.keys()):
            curr_rev, user = time_mapper[time][0], time_mapper[time][1]
            timestamp = '^^^_' + time
            if curr_rev not in rev_mapper:
                rev_mapper[curr_rev] = rev_count
                rev_count += 1
                revert_flag = 0
            else:
                revert_flag = 1
            curr_rev = rev_mapper[curr_rev]
            curr_line = '{} {} {} {}\n'.format(timestamp, revert_flag,
                                             curr_rev, user)
            lines.append(curr_line)
        fh.writelines(lines[::-1])
        del lines

def convert_tree_to_df(root, tags):

    # Initializes tags for different levels within the xml format
    curr_page_level_tags = list(tags.intersection(page_level_tags))
    curr_rev_level_tags = list(tags.intersection(rev_level_tags))
    curr_contr_level_tags = list(tags.intersection(contr_level_tags))
    curr_tags = [curr_page_level_tags, curr_rev_level_tags,
            curr_contr_level_tags]
    # Column order for output
    cols = [tag for tag_level in curr_tags for tag in tag_level]
    # Temporary matrix before dataframe
    df_lists = []

    for page_el in root.iterfind(xpath_dict['page'], namespaces=nsmap):
        curr_row = {}
        # Gets all Page level tags
        for page_tag in curr_tags[0]:
            curr_row[page_tag] = get_tag_if_exists(page_el, page_tag)
        for rev_el in page_el.iterfind(xpath_dict['revision'],
                                       namespaces=nsmap):
            # Gets all Revision level tags
            for rev_tag in curr_tags[1]:
                curr_row[rev_tag] = get_tag_if_exists(rev_el, rev_tag)
            contr_el = rev_el.find(xpath_dict['contributor'], namespaces=nsmap)
            # Gets all contributor level tags
            for contr_tag in curr_tags[2]:
                curr_row[contr_tag] = get_tag_if_exists(contr_el, contr_tag)
            df_lists.append(list(curr_row.values()))
    df = pd.DataFrame(df_lists, columns=cols)
    del df_lists
    if 'timestamp' in cols:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df

def unzip_to_txt(data_dir, fp_unzip, tags):
    temp_dir = data_dir + 'temp/'
    out_dir = data_dir + 'out/'
    fp_txt = out_dir + 'light_dump_' + fp_unzip.replace('.', '_') + '.txt'
    fp_unzip = fp_unzip
    # USAGE
    context = etree.iterparse(temp_dir + fp_unzip,
                              tag='{http://www.mediawiki.org/xml/export-0.10/}page',
                              encoding='utf-8')
    context_to_txt(context=context, fp_txt=fp_txt,
                   data_dir=data_dir, tags=tags)

    # Delete etree and unzipped file
    del context
    print('Done with ' + temp_dir + fp_unzip)

def get_files_from_url(url, raw_dir):
    if url.split('.')[-1] == '7z':
        # Registers format to .7zip
        try:
            shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)
            print('.7z registered for "7zip"')
        except:
            print('.7z is already registered for "7zip"')

    zip_fp = url.split('/')[-1]
    if not os.path.exists(raw_dir + zip_fp):
        urlretrieve(url, raw_dir + zip_fp)
    else:
        print('Already have zipped file in disk. Skipping download')
    return zip_fp

    # with urlopen(zipurl) as zipresp, NamedTemporaryFile() as tfile:
    #     tfile.write(zipresp.read())
    #     tfile.seek(0)
    #     shutil.unpack_archive(tfile.name, temp_dir)

def unpack_zip(raw_dir, temp_dir, fp_zip):
    # Unzips the current file
    prev_files = set(os.listdir(temp_dir))
    if fp_zip.split('.')[-1] == '7z':
        shutil.unpack_archive(raw_dir + fp_zip, temp_dir)
    else:
        try:
            ZipFile(raw_dir + fp_zip).extractall(path=temp_dir)
        except BadZipfile:
            print('File already unpacked')
            shutil.move(raw_dir + fp_zip, temp_dir + fp_zip)
            fp_unzip = fp_zip
            print('Unzipped file path:', temp_dir + fp_unzip)
            return fp_unzip

    print('Unzipped', raw_dir + fp_zip, 'to', temp_dir)

    fp_unzip = (set(os.listdir(temp_dir)) - prev_files).pop()

    print('Unzipped file path:', temp_dir + fp_unzip)
    return fp_unzip

def remove_dir(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)

# ---------------------------------------------------------------------
# Helper Functions for Getting M-Statistic
# ---------------------------------------------------------------------
def get_m_stat(rev_order, editor_order, num_edits_dict):
    # Reverses based on reading from latest revision
    rev_order = rev_order[::-1]
    editor_order = editor_order[::-1]

    # Revisions start at 1
    next_val = 1
    # Maps revision to index
    rev_map = {}
    # Tracks number of m values
    m_val_dict = {}
    # Tracks editors to who they reverted
    mutual_revs = {}
    # Tracks total number of mutual reverts
    mutual_revs_editors = set()
    max_m_val = 0

    # Iterate across the revisions
    for i in range(len(rev_order)):
        # Runs when revision is a revert
        if rev_order[i] < next_val:
            try:
                # Previous editor maps from the rev_map to the index of
                # the editor in the editor_order list, plus one for the offset
                prev_editor = editor_order[rev_map[rev_order[i]] + 1]

                # Ignore case of consecutive versions from previous edit
                if i + 1 < len(rev_order) and rev_order[i + 1] == rev_order[i]:
                    continue

                # Current editor will be at the same index as in rev_order
                curr_editor = editor_order[i]

                # Ignore case of editor reverting themselves
                if prev_editor == curr_editor:
                    continue
                # Minimum of the number of the edits between the editors
                curr_m_val = min(num_edits_dict[prev_editor],
                                num_edits_dict[curr_editor])
                # Updates maximum value
                max_m_val = max(max_m_val, curr_m_val)

                # Adds value to a dictionary to maintain quick updates
                if curr_m_val not in m_val_dict:
                    m_val_dict[curr_m_val] = 0
                m_val_dict[curr_m_val] += 1

                # Updates E value -> number of mutual revert editors
                if curr_editor not in mutual_revs:
                    mutual_revs[curr_editor] = set()
                mutual_revs[curr_editor].add(prev_editor)
                if prev_editor in mutual_revs and\
                    curr_editor in mutual_revs[prev_editor]:
                    mutual_revs_editors.add(curr_editor)
                    mutual_revs_editors.add(prev_editor)
            except KeyError:
                continue
            except:
                e = sys.exc_info()
                print(e)
        else:
            # Maps the revision number to the index in the
            # rev_order/editor_order list
            rev_map[rev_order[i]] = i
            next_val += 1
    # Edge case when no mutual edits
    if not len(m_val_dict):
        return 0
    # Remove maximum pair(s)
    del m_val_dict[max_m_val]
    # Calculates M-Statistic
    m_stat_val = (sum([k * v for k, v in m_val_dict.items()]) *
                  len(mutual_revs_editors))
    return m_stat_val

def update_line(line, editor_mapper, editor_count, num_edits_dict,
                editor_order, rev_order):
    line = line.split()
    if line[3] not in editor_mapper:
        editor_mapper[line[3]] = editor_count
        num_edits_dict[editor_mapper[line[3]]] = 0
        editor_count += 1
    num_edits_dict[editor_mapper[line[3]]] += 1
    editor_order.append(editor_mapper[line[3]])
    rev_order.append(int(line[2]))
    return editor_count

def grab_m_stat_over_time(raw_data, data_dir='data/'):
    """
    Intended for only getting the M-Statistic over time for plotting
    Used when raw_data is just one file with the history of just one page
    :param raw_data: The raw light dump file with just one article
    :param data_dir: The directory for output
    :return: None
    """
    # File location for resulting M-Statistic over time
    page_id_write_obj = open(data_dir + 'out/overtime_' +
            raw_data.split('/')[-1].replace('.txt', '.csv'),
            'w+', newline='')
    page_id_fp_csv_writer = writer(page_id_write_obj)

    # Initializes for no good reason
    editor_order, num_edits_dict, editor_mapper, rev_order, editor_count = \
        [], {}, {}, [], 0

    line_num = -1
    page_id_fp_csv_writer.writerow(['Timestamp', 'M-Statistic'])
    # Iterates through each line in the light dump file
    for line in reversed(list(open(raw_data))):
        line_num += 1
        # Removes end newline characters
        line = line.rstrip()

        # Start of next page
        if '^^^' != line[:3]:
            continue

        editor_count = update_line(line, editor_mapper, editor_count,
                                   num_edits_dict, editor_order, rev_order)
        m_stat_val = get_m_stat(rev_order[::-1], editor_order[::-1],
                num_edits_dict)
        page_id_fp_csv_writer.writerow([
            pd.to_datetime(line.split()[0][4:]), m_stat_val
            ])
    print('Done')

# ---------------------------------------------------------------------
# Driver Function for GETTING DATA
# ---------------------------------------------------------------------

def get_data(
        data_dir='data/',
        fps=(
            'https://dumps.wikimedia.org/enwiki/20200101/enwiki-20200101-pages-meta-history1.xml-p10p1036.7z',
            'https://dumps.wikimedia.org/enwiki/20200101/enwiki-20200101-pages-meta-history1.xml-p1037p2031.7z'
        ),
        fp_type=0
    ):

    child_dirs = ['', 'out/', 'temp/', 'test/', 'raw/']
    for child_dir in child_dirs:
        if not os.path.exists(data_dir + child_dir):
            os.makedirs(data_dir + child_dir)
    raw_dir = data_dir + 'raw/'
    temp_dir = data_dir + 'temp/'

    print('Directories are made/were made')

    fp_unzips = []
    for zip_file in fps:
        fp_zip = zip_file
        if fp_type == 0:
            print('Using urls for files, so going to download them now')
            print('Starting first fp:', fp_zip)
            print('Downloading zip from url')
            fp_zip = get_files_from_url(url=fp_zip,
                                        raw_dir=raw_dir)
            print('Done downloading zip.')
        elif fp_type == 1:
            print('File already downloaded : - )')
            if fp_zip not in os.listdir(raw_dir):
                shutil.copyfile(data_dir + fp_zip,
                                raw_dir + fp_zip.split('/')[-1])
        print('Now unpacking/unzipping zip.')
        fp_unzip = unpack_zip(raw_dir=raw_dir, temp_dir=temp_dir,
                              fp_zip=fp_zip)
        fp_unzips.append(fp_unzip)
        print('Done unzipping.')
    print('Done. The unzipped files are:', fp_unzips)
    return

# ---------------------------------------------------------------------
# Driver Function for PROCESSING DATA
# ---------------------------------------------------------------------

def process_data(
        data_dir = 'data/',
        fps = (
            'enwiki-20200101-pages-meta-history1.xml-p10p1036',
            'enwiki-20200101-pages-meta-history1.xml-p1037p2031'
        ),
        tags={'page_title', 'rev_id', 'parent_id', 'username', 'user_ip'}
    ):

    for fp_unzip in fps:
        unzip_to_txt(data_dir=data_dir, fp_unzip=fp_unzip, tags=tags)

# ---------------------------------------------------------------------
# Driver Function for ANALYZING DATA
# ---------------------------------------------------------------------

def analyze_m_stat_data(data_dir='data/',
                 raw_data='en_wiki.txt'):

    out_dir = data_dir + 'out/'
    # Resulting M statistic
    page_id_write_obj = open(out_dir + 'm_stat_' + raw_data,
            'w+', newline='')
    page_id_fp_csv_writer = writer(page_id_write_obj)

    # Maintain for page_id
    page_count = 0

    # Starter csv header
    title_id, title, m_stat_val = 'Title_ID', 'Title', 'Statistic'

    # Initializes for no good reason
    editor_order, num_edits_dict, editor_mapper, rev_order, editor_count = \
        [], {}, {}, [], 0

    line_num = -1
    # Iterates through each line in the light dump file
    for line in open(out_dir + raw_data):
        line_num += 1
        # Removes end newline characters
        line = line.rstrip()

        # Start of next page
        if '^^^' != line[:3]:
            if not m_stat_val:
                m_stat_val = get_m_stat(rev_order, editor_order, num_edits_dict)
            page_id_fp_csv_writer.writerow([title_id, title, m_stat_val])

            title_id, title, m_stat_val = page_count, line, None
            page_count += 1
            if not page_count % 100000:
                print('Done parsing', page_count, 'pages')

            editor_order, num_edits_dict, editor_mapper, rev_order =\
                [], {}, {}, []
            editor_count = 0
            continue

        editor_count = update_line(line, editor_mapper, editor_count,
                                   num_edits_dict, editor_order, rev_order)
    if not m_stat_val:
        m_stat_val = get_m_stat(rev_order, editor_order, num_edits_dict)
        page_id_fp_csv_writer.writerow([title_id, title, m_stat_val])
    print('Done')
