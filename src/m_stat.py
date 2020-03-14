import sys
import pandas as pd
from csv import writer


# ---------------------------------------------------------------------
# Helper Functions for Getting M-Statistic
# ---------------------------------------------------------------------
def get_m_stat(rev_order, editor_order, num_edits_dict, extra_stats):
    """
    Gets the M-Statistic and possibly extra statistics from the order of \
    revisions, order of editors, and the number of edits for each editor in a
    given article
    :param rev_order: Order of revisions/edits
    :param editor_order: Order of editors
    :param num_edits_dict: Map each editor to respective number of edits
    :param extra_stats: Flag for extra statistics
    :return: M-Statistic
    """
    # Reverses because light dump is in descending order
    # (i.e. latest to earliest)
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
        # Reverts point to previous edits, so it should have a smaller revision
        # number than if it were to incrementally increase if it were a normal
        # edit
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
                if (prev_editor in mutual_revs and
                        curr_editor in mutual_revs[prev_editor]):
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
    num_reverts = sum(m_val_dict.values())
    # Remove maximum pair(s)
    del m_val_dict[max_m_val]
    # Calculates M-Statistic
    res_stats = []
    m_stat = [sum([k * v for k, v in m_val_dict.items()]) *
                  len(mutual_revs_editors)]
    res_stats.append(m_stat)
    if extra_stats:
        res_stats.extend([len(rev_order), num_reverts, len(set(editor_order)),
                          len(mutual_revs_editors)])
    return res_stats


def update_line(line, editor_mapper, editor_count, num_edits_dict,
                editor_order, rev_order):
    """
    Updates various tracking dictionaries for future use in calculating
    M-Statistic with values extracted from a line in the light dump data
    Example light dump formatted line:
        ^^^_2019-05-17T01:24:12Z 0 493 JJMC89
        ^^^[datetime] [flag for revert] [edit number] [editor name/IP address]
    We only really need the edit number and editor name/IP address, which
    can be reasoned in get_m_stat()
    :param line: Current line in light dump
    :param editor_mapper: Maps editors to a unique identifier
    :param editor_count: Number of editors seen thus far in an article
    :param num_edits_dict: Maps editor id to number of respective edits
    :param editor_order: Ordering so far of editor
    :param rev_order: Revision order
    :return: Updated number of editors
    """
    line = line.split()
    if line[3] not in editor_mapper:
        editor_mapper[line[3]] = editor_count
        num_edits_dict[editor_mapper[line[3]]] = 0
        editor_count += 1
    num_edits_dict[editor_mapper[line[3]]] += 1
    editor_order.append(editor_mapper[line[3]])
    rev_order.append(int(line[2]))
    return editor_count


# ---------------------------------------------------------------------
# Driver Function for GETTING M_STATISTICS
# ---------------------------------------------------------------------

def get_m_stat_data(data_dir='data/',
                    fps=
                    ("light-dump-enwiki-20200101-pages-meta-history1-" +
                     "xml-p10p1036.txt",
                     "light-dump-enwiki-20200101-pages-meta-history1-" +
                     "xml-p1037p2031.txt"),
                    extra_stats=False
                    ):
    """
    Gets the M-Statistic for each article in the light dump formatted data
    :param data_dir: directory where the data lies within : - )
    :param fps: Filepaths
    :param extra_stats: Flag for extra statistics
    """

    out_dir = '{}out/'.format(data_dir)
    out_m_stat_dir = '{}out_m_stat/'.format(data_dir)

    # Maintain for page_id
    page_count = 0

    # Iterate through filepaths
    for fp in fps:
        # Writer for current filepath
        page_id_write_obj = \
            open(
                '{}m-stat-{}'.format(
                    out_m_stat_dir,
                    fp.replace('.txt', '.csv').replace('light-dump-', '')
                ),
                'w', newline=''
            )
        page_id_fp_csv_writer = writer(page_id_write_obj)

        # Starter csv header
        title_id, title, m_stats = 'Title_ID', 'Title', ['M-Statistic']
        if extra_stats:
            m_stats.extend(['Num Edits', 'Nums Reverts', 'Num Editors',
                            'Num Mutual Editors'])

        # Initializes for no good reason
        editor_order, num_edits_dict, editor_mapper, rev_order, editor_count =\
            [], {}, {}, [], 0

        line_num = -1
        # Iterates through each line in the light dump file
        for line in open(out_dir + fp):
            line_num += 1
            # Removes end newline characters
            line = line.rstrip()

            # Passes at the start of the next article
            if '^^^' != line[:3]:
                next_row = [title_id, title]
                # Calculates M-Statistic
                if not m_stats:
                    m_stats = get_m_stat(rev_order, editor_order,
                                         num_edits_dict, extra_stats)
                next_row.extend(m_stats)
                # Writes article_id, title, and M-Statistic to file
                page_id_fp_csv_writer.writerow(next_row)

                # Sets up for next article
                title_id, title, m_stat_val = page_count, line, None
                editor_order, num_edits_dict, editor_mapper, rev_order = \
                    [], {}, {}, []
                editor_count = 0
                page_count += 1
                if not page_count % 100000:
                    print('Done parsing', page_count, 'pages')
                continue

            # Updates the necessary information used to calculate the M-Stat
            editor_count = update_line(line, editor_mapper, editor_count,
                                       num_edits_dict, editor_order, rev_order)

        # Last article edge case
        if not m_stats:
            next_row = [title_id, title]
            m_stats = get_m_stat(rev_order, editor_order, num_edits_dict)
            next_row.extend(m_stats)
            page_id_fp_csv_writer.writerow(next_row)

        print('Done with {}!'.format(fp))


# ---------------------------------------------------------------------
# Driver Function for GETTING M STATISTIC OVER TIME
# ---------------------------------------------------------------------

def grab_m_stat_over_time(data_dir='data/',
                          fps=('light-dump-Anarchism.txt',
                               'light-dump-Abortion.txt')):
    """
    Intended for only getting the M-Statistic over time for plotting
    Used when raw_data is just one file with the history of just one page
    :param fps: The raw light dump filepaths with just one article each
    :param data_dir: The directory for output
    :return: None
    """

    out_dir = '{}out/'.format(data_dir)
    out_m_stat_dir = '{}out_m_stat/'.format(data_dir)

    for fp in fps:
        # File location for resulting M-Statistic over time
        page_id_write_obj = \
            open('{}overtime-{}'.format(
                out_m_stat_dir,
                fp.replace('.txt', '.csv').replace('light-dump-', '')
            ), 'w+', newline=''
            )
        page_id_fp_csv_writer = writer(page_id_write_obj)

        editor_order, num_edits_dict, editor_mapper, rev_order, editor_count = \
            [], {}, {}, [], 0

        line_num = -1
        page_id_fp_csv_writer.writerow(['Timestamp', 'M-Statistic'])
        # Iterates through each line in the light dump file
        for line in reversed(list(open(out_dir + fp))):
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
        print('Done with', fp)
