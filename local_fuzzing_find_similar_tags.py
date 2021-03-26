import itertools
import csv
import sys

import inquirer
from rapidfuzz import fuzz

def write_output_csv(filename, output_lod, headers):
    filename = filename + ".csv" if ".csv" not in filename else filename

    with open("Output " + filename, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, headers)
        dict_writer.writeheader()
        dict_writer.writerows(output_lod)
    print("Write to csv was successful\n")


def read_input_csv(filename, **kwargs):
    filename = filename + ".csv" if ".csv" not in filename else filename

    with open(filename) as f:
        file_lod = [{k:v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)] # LOD

    print(f"Length of input CSV is: {len(file_lod)}")

    if kwargs.get("columns") and any(x for x in kwargs["columns"] if x not in file_lod[0].keys()):
        sys.exit(f"Exiting. Your CSV needs to have these columns: {kwargs['columns']}")

    if kwargs.get("start_row"):
        file_lod = file_lod[kwargs["start_row"]:]

    if kwargs.get("url_column"):
        file_lol = [x[kwargs["url_column"]] for x in file_lod if is_url(x[kwargs["url_column"]])] # throw out empty cells
        print(f"Length of input CSV after removing non-URL rows and accounting for start_at is: {len(file_lol)}")
        return file_lol

    print(f"Length of input CSV after accounting for start_at is: {len(file_lod)}")
    return file_lod


def allow_user_to_deny_matching(message):

    questions = [inquirer.Text("approval", message=message)]
    answers = inquirer.prompt(questions)
    if answers["approval"] in ["No", "no", "N", "n", "M", "m"]:
        print('disapproved')
        return False
    if answers["approval"] in ["k", "K", "l", "L"]:
        print('alt')
        return "alt"
    else:
        return True


# 90 -> different suffixes, pluralizing, etc
# 80 - pretty close concepts, some false positives (ebay integrationa dn Xero integration)
def find_similar_pairs(tags, *, required_similarity=80):
    """
    Find pairs of similar-looking tags in the collection ``tags``.

    Increase ``required_similarity`` for stricter matching (=> less results).
    """
    for t1, t2 in itertools.combinations(sorted(tags), 2):
        if fuzz.ratio(t1, t2) > required_similarity:
            yield (t1, t2)


def fuzzy_match_with_counts(output_lod, already_tagged, t1, t2, t1_index, t2_index):
    t1_count = int(output_lod[t1_index]["Count"])
    t2_count = int(output_lod[t2_index]["Count"])

    if t1_count >= t2_count:
        preferable_tag, discarded_tag = t1, t2
        message = f" {t1} ({t1_count}) for {t2} ({t2_count})"
    else:
        preferable_tag, discarded_tag = t2, t1
        message = f" {t2} ({t2_count}) for {t1} ({t1_count})"

    if t1.lower().strip() == t2.lower().strip():
        print("the only difference was casing")
        output_lod[t1_index]["Applied_Tag"] = preferable_tag
        output_lod[t2_index]["Applied_Tag"] = preferable_tag

    approval = allow_user_to_deny_matching(message)
    if not approval:
        return output_lod
    elif approval == "alt":
        preferable_tag, discarded_tag = discarded_tag, preferable_tag

    output_lod[t1_index]["Applied_Tag"] = preferable_tag
    output_lod[t2_index]["Applied_Tag"] = preferable_tag
    already_tagged.append(discarded_tag)

    return output_lod, already_tagged

def fuzzy_match_basic(output_lod, already_tagged, t1, t2, t1_index, t2_index):

    message = f" {t2} <> {t1}"
    if t1 == t2:
        message += " - they are exactly the same"
    elif t1.lower() == t2.lower():
        message += " - they are cased differently"
    elif t1.strip() == t2.strip():
        message += " - they are spaced differently"
    elif t1.lower().strip() == t2.lower().strip():
        message += " - they are both cased differently and spaced differently"

    approval = allow_user_to_deny_matching(message)

    if approval:
        output_lod[t1_index]['message'] = message
        output_lod[t1_index]['Applied_Tag'] = t2
        already_tagged.append(discarded_tag)

    return output_lod, already_tagged





if __name__ == "__main__":
    filename = "SS Tags - 3.25.21 Post MDD.csv"
    similarity = 85
    TAG_COL = "product_name"
    COUNT_COL = None
    columns = [TAG_COL, COUNT_COL] if COUNT_COL else [TAG_COL]
    START_ROW = 1990

    input_lod = read_input_csv(filename, columns=columns, start_row=START_ROW) #, "Count"

    output_lod = [x for x in input_lod if x.get(TAG_COL)] # throw out empty rows
    if COUNT_COL:
         output_lod = [x for x in input_lod if x.get("Count")]

    output_headers = list(output_lod[0].keys()) + ["Applied_Tag"]
    tags = [x.get(TAG_COL) for x in output_lod]


    counter = 0
    already_tagged = []
    tag_pairs = find_similar_pairs(tags, required_similarity=similarity)

    for t1, t2 in tag_pairs:
        if t1 in already_tagged or t2 in already_tagged:
            print("Already tagged; skipping")
            continue

        counter += 1

        t1_index = tags.index(t1)
        t2_index = tags.index(t2)

        if COUNT_COL:
            output_lod, already_tagged = fuzzy_match_with_counts(output_lod, already_tagged, t1, t2, t1_index, t2_index)
        else:
            output_lod, already_tagged = fuzzy_match_basic(output_lod, already_tagged, t1, t2, t1_index, t2_index)


        if counter != 0 and counter % 25 == 0:
            print(f"Now on row number {t1_index}")
            write_output_csv("Output " + filename, output_lod, output_headers)

    print(f"Count of pairings assessed: {counter}")

    if not COUNT_COL:
        output_headers.append("message")

    write_output_csv("Output " + filename, output_lod, output_headers)

