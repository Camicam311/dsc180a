from urllib.request import urlretrieve
from zipfile import ZipFile, BadZipfile
from lxml import etree
from copy import deepcopy
from py7zr import unpack_7zarchive
import shutil
import os
import pandas as pd

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
rev_level_tags = {'rev_id', 'parent_id', 'timestamp', 'comment', 'model',
                  'format', 'edit', 'sha1'}
contr_level_tags = {'username', 'user_id', 'user_ip'}

nsmap = {'ns': 'http://www.mediawiki.org/xml/export-0.10/'}


# ---------------------------------------------------------------------
# Helper Functions for Getting Data
# ---------------------------------------------------------------------

def context_to_txt(context, fp_txt, out_dir, tags, out_format,
                   page_chunk=5):
    """
    Converts the XML Tree context to some text format
    Either csv or light format
    :param context: XML iterable context for streaming
    :param fp_txt: File path for output
    :param out_dir: Output directory
    :param tags: Tags used for csv format
    :param out_format: Format flag (0 for light_format, otherwise csv)
    :param page_chunk: Number of pages per chunk
    """

    if out_format == 0:
        light_format = True
    else:
        light_format = False

    # create an empty tree to add XML elements to ('pages')
    tree = etree.ElementTree()
    root = etree.Element("wikimedia")

    page_num = 1

    # loop through the large XML tree (streaming)
    for event, elem in context:
        # After a given number of pages, write the tree to the XML file
        # and reset the tree / create a new file.
        if page_num % page_chunk == 0:
            tree, root = write_tree_to_txt(
                tree=tree, root=root, page_num=page_num, fp_txt=fp_txt,
                out_dir=out_dir, tags=tags, light_format=light_format
            )

        # add the 'page' element to the small tree
        root.append(deepcopy(elem))
        page_num += 1

        # release unneeded XML from memory
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    # Edge case for extra pages in memory
    if page_num % page_chunk:
        write_tree_to_txt(
                tree=tree, root=root, page_num=page_num, fp_txt=fp_txt,
                out_dir=out_dir, tags=tags, light_format=light_format
                )
    del context


def write_tree_to_txt(tree, root, page_num, fp_txt, out_dir, tags,
                      light_format=True):
    """
    Writes tree to csv file
    :param tree: Etree
    :param root: Root node of tree
    :param page_num: Last page encoded within the tree
    :param fp_txt: File path of the txt file
    :param out_dir: Data directory for output
    :param tags: Tags used for output
    :param light_format: Whether or not to output light format
    :return:
    """
    print('Begin conversion just up to {}'.format(page_num))
    # If desired output is in light dump format
    if light_format:
        convert_tree_light_format(root=root, out_dir=out_dir, fp_txt=fp_txt)
        print('converted up to {}'.format(page_num))
        return etree.ElementTree(), etree.Element("wikimedia")

    df = convert_tree_to_df(root=root, tags=tags)
    print('converted up to {}'.format(page_num))
    if not os.path.exists(out_dir + fp_txt):
        df.to_csv(out_dir + fp_txt, index=False)
        print('converted up to {} to csv'.format(page_num))
    else:
        df.to_csv(out_dir + fp_txt, mode='a', index=False, header=False)
        print('appended up to {} to csv'.format(page_num))
    del tree, root, df
    return etree.ElementTree(), etree.Element("wikimedia")


def get_tag_if_exists(parent, tag):
    """
    Checks if tag is a child of the parent in the XML tree
    If so, gets the Wikipedia tag format
    :param parent: Parent node in XML tree
    :param tag: Desired child tag
    :return: Text within the XML tag OR None
    """
    res = parent.find(xpath_dict[tag], namespaces=nsmap)
    try:
        return res.text
    except:
        # When tag is not child of parent and res = None
        return res


def convert_tree_light_format(root, out_dir, fp_txt):
    """
    Converts from the XML tree to light formatted data
    Example formatting:
        Anarchism
        ^^^_2019-05-17T01:24:12Z 0 493 JJMC89

        [Page title]
        ^^^[datetime] [flag for revert] [edit number] [editor name/IP address]
    :param root: Root of tree
    :param out_dir: Output directory
    :param fp_txt: Filepath for output
    """
    # File Handle
    fh = open(out_dir + fp_txt, 'a')
    # Only necessary columns
    cols = ['timestamp', 'edit', 'username']

    # Iterates through every page under the current root
    for page_el in root.iterfind(xpath_dict['page'], namespaces=nsmap):
        page_title = get_tag_if_exists(page_el, 'page_title')
        fh.write(page_title + '\n')

        # Keeps of edits by their time
        # Tragically ugly but necessary because raw dumps are not in
        # chronological order
        time_mapper = {}
        for rev_el in page_el.iterfind(xpath_dict['revision'],
                                       namespaces=nsmap):
            # Grabs necessary information: time, edit text, username/ip
            timestamp = get_tag_if_exists(rev_el, cols[0])
            curr_rev = get_tag_if_exists(rev_el, cols[1])
            contr_el = rev_el.find(xpath_dict['contributor'], namespaces=nsmap)
            user = get_tag_if_exists(contr_el, cols[2])
            if not user:
                user = get_tag_if_exists(contr_el, 'user_ip')
            if user:
                # Any spaces in usernames are replaced with underscores
                user = user.replace(' ', '_')
            curr_line = (curr_rev, user)
            # Maps every time to the (edit, username/IP address)
            time_mapper[timestamp] = curr_line

        # Rev_mapper keeps track of each revision's text because that's
        # how each revert is tracked
        # (WHICH IS SUPER FUCKING SPACE INEFFICIENT. BUT IDK, DOES ANYONE HAVE
        # A BETTER FUCKING IDEA. FUCKING CS NIGHTMARE HERE. WIKIMEDIA NEEDS TO
        # FIX THIS SHIT)
        rev_mapper, rev_count, lines =\
            {}, 1, []
        # Iterates across each edit in chronological order
        for time in sorted(time_mapper.keys()):
            curr_rev, user = time_mapper[time][0], time_mapper[time][1]
            timestamp = '^^^_' + time
            # Checks if edit was seen before and thus it was a revert
            if curr_rev not in rev_mapper:
                # Adds new edit to dictionary that maps each edit's text
                # to their revision ID number
                rev_mapper[curr_rev] = rev_count
                rev_count += 1
                revert_flag = 0
            else:
                revert_flag = 1
            curr_rev = rev_mapper[curr_rev]
            curr_line = '{} {} {} {}\n'.format(timestamp, revert_flag,
                                               curr_rev, user)
            lines.append(curr_line)
        # Reverses for descending order
        fh.writelines(lines[::-1])
        del lines


def convert_tree_to_df(root, tags):
    """
    Converts the XML tree to a dataframe with each tag as a column
    :param root: Root of current XML tree
    :param tags: Desired tags
    :return: Dataframe
    """
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


def unzip_to_txt(data_dir, fp_unzip, tags, out_format):
    """
    Unzips file to desired output format
    Currently supports only csv or light dump format
    :param data_dir: Directory for all data
    :param fp_unzip: File path of unzipped file
    :param tags: Desired tags for csv format
    :param out_format: Output format (0 for light dump, otherwise csv)
    """
    temp_dir = '{}temp/'.format(data_dir)
    out_dir = '{}out/'.format(data_dir)
    fp_txt = 'light-dump-{}.txt'.format(fp_unzip.replace('.', '-'))
    context = etree.iterparse(temp_dir + fp_unzip,
                              tag='{http://www.mediawiki.org/' +\
                                  'xml/export-0.10/}page',
                              encoding='utf-8', huge_tree=True)
    print('Converting to txt')
    context_to_txt(context=context, fp_txt=fp_txt, out_dir=out_dir,
                   tags=tags, out_format=out_format)

    # Delete etree
    del context
    print('Done with ' + temp_dir + fp_unzip)


def get_files_from_url(url, raw_dir):
    """
    Downloads file from url
    :param url: URL for file
    :param raw_dir: Directory for raw data
    :return: Returns file path for created file
    """
    zip_fp = url.split('/')[-1]
    if not os.path.exists(raw_dir + zip_fp):
        urlretrieve(url, raw_dir + zip_fp)
    else:
        print('Already have zipped file in disk. Skipping download')
    return zip_fp


def unpack_zip(raw_dir, temp_dir, fp_zip):
    """
    Unpacks a zip file
    Supports .7z and .zip
    :param raw_dir: Directory for raw data containing zipped file
    :param temp_dir: Directory for temporary data for unzipped file
    :param fp_zip: File path of zipped file
    :return: file path of unzipped file
    """
    # Unzips the current file
    if fp_zip.split('.')[-1] == '7z':
        # Registers format to .7zip
        try:
            shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)
            print('.7z registered for "7zip"')
        except:
            print('.7z is already registered for "7zip"')
        shutil.unpack_archive(raw_dir + fp_zip, temp_dir)
    else:
        try:
            ZipFile(raw_dir + fp_zip).extractall(path=temp_dir)
        except BadZipfile:
            print('File already unpacked')
            shutil.copy(raw_dir + fp_zip, temp_dir + fp_zip)
            fp_unzip = fp_zip
            print('Unzipped file path:', temp_dir + fp_unzip)
            return fp_unzip

    print('Unzipped', raw_dir + fp_zip, 'to', temp_dir)

    fp_unzip = max([temp_dir + file for file in os.listdir(temp_dir)],
                   key = os.path.getctime)

    print('Unzipped file path:', temp_dir + fp_unzip)
    return fp_unzip


def remove_dir(dir_to_remove):
    """
    Removes directory
    :param dir_to_remove: Directory to remove
    """
    shutil.rmtree(dir_to_remove, ignore_errors=True)


def get_basic_data_dirs(data_dir='data/',
                        child_dirs=('', 'out/', 'temp/', 'raw/',
                                    'out_m_stat/')):
    """
    Adds desired sub-directories to parent data directory
    :param data_dir: Directory for data
    :param child_dirs: Sub-directories for where data actually exists within
    """
    for child_dir in child_dirs:
        if not os.path.exists(data_dir + child_dir):
            os.makedirs(data_dir + child_dir)


# ---------------------------------------------------------------------
# Driver Function for EXTRACTING AND UNZIPPING COMPRESSED DATA/URLS
# ---------------------------------------------------------------------

def get_data(
        data_dir='data/',
        fps=(
            'https://dumps.wikimedia.org/enwiki/20200101/' +
            'enwiki-20200101-pages-meta-history1.xml-p10p1036.7z',
            'https://dumps.wikimedia.org/enwiki/20200101/' +
            'enwiki-20200101-pages-meta-history1.xml-p1037p2031.7z'
        ),
        fp_type=0,
        unzip_type=0
):
    """
    Gets the data from either a url or some file destination and unzips
    the file. If file is passed in, function will copy the file over to the
    raw data directory within the directory containing data
    :param data_dir: Directory for data
    :param fps: Filepaths/URLs for downloading and unzipping
    :param fp_type: 0 for URL, 1 for actual file
    :param unzip_type: If the unzipped file is already in a desired format
                       (i.e. light dump format)
                       0 for light dump format -> directly to output directory
                       otherwise for XML format -> redirect to temp directory
    :return: None
    """

    child_dirs = ['', 'out/', 'temp/', 'raw/', 'out_m_stat/']
    get_basic_data_dirs(data_dir, child_dirs)
    raw_dir = data_dir + 'raw/'
    temp_dir = data_dir + 'temp/'
    out_dir = data_dir + 'out/'

    print('Directories are made/were made')

    fp_unzips = []
    for fp_zip in fps:
        if fp_type == 0:
            print('Using urls for files, so going to download them now')
            print('Starting first fp:', fp_zip)
            print('Downloading zip from url')
            fp_zip = get_files_from_url(url=fp_zip,
                                        raw_dir=raw_dir)
            print('Done downloading zip.')
        elif fp_type == 1:
            print('File already downloaded : - )')
            # Copies file to raw directory if not there yet
            if fp_zip not in os.listdir(raw_dir):
                if fp_zip in os.listdir(data_dir):
                    shutil.copyfile(data_dir + fp_zip,
                                    raw_dir + fp_zip.split('/')[-1])
                else:
                    shutil.copyfile(fp_zip,
                                    raw_dir + fp_zip.split('/')[-1])
                    fp_zip = fp_zip.split('/')[-1]
        print('Now unpacking/unzipping zip.')
        # Directs unzip file to desired sub-directory
        if not unzip_type:
            fp_unzip = unpack_zip(raw_dir=raw_dir, temp_dir=temp_dir,
                                  fp_zip=fp_zip)
        else:
            fp_unzip = unpack_zip(raw_dir=raw_dir, temp_dir=out_dir,
                                  fp_zip=fp_zip)
        fp_unzips.append(fp_unzip)
        print('Done unzipping.')
    print('Done. The unzipped files are:', fp_unzips)
    return


# ---------------------------------------------------------------------
# Driver Function for CONVERTING UNZIPPED XML FILE TO READABLE FORMATS
# ---------------------------------------------------------------------

def process_data(
        data_dir='data/',
        fps=(
            'enwiki-20200101-pages-meta-history1.xml-p10p1036',
            'enwiki-20200101-pages-meta-history1.xml-p1037p2031'
        ),
        tags=('page_title', 'rev_id', 'parent_id', 'username', 'user_ip'),
        out_format=0
):
    """
    Processes the XML file into more readable formats
    Output formats possible are light dump format or csv format
    :param data_dir: Directory for data
    :param fps: List of file paths
    :param tags: XML tags to store for csv format
    :param out_format: Output format, 0 for light dump format, otherwise csv
    """

    if not isinstance(tags, set):
        try:
            tags = set(tags)
        except TypeError:
            print("Tags needs to be a iterable, like the default:" +
                  "{'page_title', 'rev_id', 'parent_id', 'username'," +
                  "'user_ip'}. Try again")

    for fp_unzip in fps:
        print('Starting with {}'.format(fp_unzip))
        unzip_to_txt(data_dir=data_dir, fp_unzip=fp_unzip, tags=tags,
                     out_format=out_format)


# ---------------------------------------------------------------------
# Driver Function for EXTRACTING SPECIFIC ARTICLES FROM LIGHT DUMP DATA
# ---------------------------------------------------------------------

def extract_article(
        data_dir='data/',
        fps=(
        "light-dump-enwiki-20200201-pages-meta-history1-xml-p10p1036.txt",
        ),
        desired_articles=('Anarchism', 'Barack Obama')
):
    """
    Extracts a desired article from a list of light dump files
    :param data_dir: Directory for data
    :param fps: List of light dump formatted files' paths
    :param desired_articles: Desired article titles
    """

    out_dir = '{}out/'.format(data_dir)
    desired_articles = set(desired_articles)
    curr_article_desired, curr_lines = None, []

    # Iterate through filepaths
    for fp in fps:
        curr_article_desired, curr_lines = None, []
        # Iterates through each line in the light dump file
        for line in open(out_dir + fp):

            # Passes through at the start of the next article
            if '^^^' != line[:3]:
                # Writes article text to file
                if curr_article_desired:
                    desired_article_out_fp =\
                        '{}light-dump-{}.txt'.format(
                            out_dir,
                            curr_article_desired.replace(' ', '-')
                            .replace('_', '-')
                        )
                    with open(desired_article_out_fp, 'w+') as curr_fh:
                        for curr_line in curr_lines:
                            curr_fh.write(curr_line)
                    print('Extracted {} to {}'.format(curr_article_desired,
                                                      desired_article_out_fp))
                    curr_article_desired, curr_lines = False, []
                    # When completed all extraction and can stop early
                    if not len(desired_articles):
                        print('Completed extraction!')
                        return
                line = line.rstrip()

                # If next article in light dump is a desired article
                if line in desired_articles:
                    curr_article_desired = line
                    print('Beginning extraction of', line)
                    desired_articles.remove(line)
                continue

            # Appends next line in light dump data for current article
            if curr_article_desired:
                curr_lines.append(line)

    # Writes article text to file
    if curr_article_desired:
        desired_article_out_fp = \
            '{}light-dump-{}.txt'.format(
                out_dir, curr_article_desired.replace(' ', '-')
            )
        with open(desired_article_out_fp, 'w+') as curr_fh:
            for curr_line in curr_lines:
                curr_fh.write(curr_line)
        print('Extracted {} to {}'.format(curr_article_desired,
                                          desired_article_out_fp))

    # For all articles not found in the extraction process
    for desired_article in desired_articles:
        print('Could not extract', desired_article)
