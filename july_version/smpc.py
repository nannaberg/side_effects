# import pandas as pd
import pdfquery
import re
from lxml import etree
from pdfquery.cache import FileCache


# def get_indication_lines():
#     data = pdf.extract(
#         [
#             ("with_parent", 'LTPage[pageid="{}"]'.format(7)),
#             ("with_formatter", None),
#             ("box_vert", "LTTextBoxVertical"),
#             ("box_hori", "LTTextBoxHorizontal"),
#             ("line_hori", "LTTextLineHorizontal"),
#         ]
#     )


def get_location_info(pdf):
    start_page_key = "start_page"
    end_page_key = "end_page"
    max_page_index = 10
    start = None
    end = None
    for i in range(max_page_index):
        data = pdf.extract(
            [
                ("with_parent", 'LTPage[pageid="{}"]'.format(i)),
                ("with_formatter", None),
                (
                    start_page_key,
                    'LTTextLineHorizontal :contains("Therapeutic indications")',
                ),
                (
                    end_page_key,
                    'LTTextLineHorizontal :contains("Posology and method of administration")',
                ),
            ]
        )
        if data[start_page_key]:
            start = (i, data[start_page_key].attr("y0"))
        if data[end_page_key]:
            end = (i, data[end_page_key].attr("y0"))
            break
    print("start: {}, {}".format(start[0], start[1]))
    print("end: {}, {}".format(end[0], end[1]))
    return start, end


def get_indication_filter(start_y0, end_y0):
    def indication_filter():
        return (
            this.text is not None
            and float(this.get("y0", 0)) < float(start_y0)
            and float(this.get("y0", 0)) > float(end_y0)
        )

    return indication_filter


def assemble_text(ordered_data):
    full_text = ""
    for i, line in enumerate(ordered_data):
        text = line.text.strip()
        if text[-1] == ".":
            full_text += text + "\n"
        elif text == "•":
            full_text += "\n\t" + text
        else:
            full_text += text
    re.sub(r"(?<=[,])(?=[^\s])", r" ", full_text)
    return full_text


def get_indication_lines(pdf, start, end):
    if start[0] == end[0]:  # if indication contained on one page
        indication_key = "indication"
        data = pdf.pq('LTPage[pageid="{}"] *'.format(start[0])).filter(
            get_indication_filter(start[1], end[1])
        )
        # for i, line in enumerate(data):
        #     print("{}: {}, {}".format(i, line.get("index"), line.text))
        # sort first by y0 descending, then x0 ascending
        # ordered_none_data = sorted(
        #     data,
        #     key=lambda x: [x.get("y0"), 1.0 / float(x.get("x0"))],
        #     reverse=True,
        # )
        # for i, line in enumerate(ordered_none_data):
        #     if line.text:
        #         print("{}: {}, {}".format(i, line.get("index"), line.text))
        #     else:
        #         print("{}: index: {}, {}".format(i, line.get("index"), "NONE"))
        ordered_data = sorted(
            [d for d in data if d.text.strip()],
            key=lambda x: [x.get("y0"), 1.0 / float(x.get("x0"))],
            reverse=True,
        )
        # if data contains bullet points, swap position of bullet point with the above line
        for i, line in enumerate(ordered_data):
            if "•" in line.text.strip():
                # print("• was in line")
                get = ordered_data[i - 1], ordered_data[i]
                ordered_data[i], ordered_data[i - 1] = get

        # print(ordered_data)
        # for i, line in enumerate(ordered_data):
        #     print("{}: {}, {}, {}".format(i, line.get("y0"), line.get("x0"), line.text))

        return ordered_data


def get_indication_text(src):
    pdf = pdfquery.PDFQuery("docs1/" + src, parse_tree_cacher=FileCache("/tmp/"))
    pdf.load()
    # start, end = get_location_info(pdf)
    # data = get_indication_lines(pdf, start, end)
    # full_text = assemble_text(data)
    with open("xml_trees/" + "testpdf" + "xmltree.xml", "wb") as f:
        f.write(etree.tostring(pdf.tree, pretty_print=True))
    print(pdf.get_layouts())
    # with open("xml_trees/" + src[:-6] + "xmltree.xml", "wb") as f:
    #     f.write(etree.tostring(pdf.tree, pretty_print=True))
    # return full_text


# def get_ltchars(pdf):
#     data = pdf.pq('LTPage[pageid="{}"] *'.format(start[0])).filter(
#         get_indication_filter(start[1], end[1])
#     )


def main():
    sources = [
        "fortacin-epar-product-information_en.pdf",
        "lacosamide-adroiq-epar-product-information_en.pdf",
        "olanzapine-mylan-epar-product-information_en.pdf",
        "ogluo-epar-product-information_en.pdf",
    ]
    for src in sources:
        print(src)
        print("source: {}".format(src))
        print(get_indication_text("testpdf.pdf"))
        print("\n")

    # with pdfplumber.open(sources[3]) as pdf:
    # text = pdf.pages[0]
    # clean_text = text.filter(lambda obj: not (obj["object_type"] == "char" and "Bold" in obj["fontname"]))
    # print(clean_text.extract_text())
    # print(full_text)
    # print(data)


if __name__ == "__main__":
    main()
# start = float(
#     pdf.pq('LTTextLineHorizontal :contains("Therapeutic indications")').attr["y0"]
# )
# end = float(
#     pdf.pq(
#         'LTTextLineHorizontal :contains("Posology and method of administration")'
#     ).attr("y0")
# )
# print("Start y0: ", start)
# print("End y0: ", end)


# def big_elements():
#     return float(this.get("width", 0)) * float(this.get("height", 0)) > 40000


# foo = pdf.extract([("big", big_elements)])
# print(foo)

# indication_key = "indication"


# data = pdf.extract(
#     [
#         ("with_formatter", None),
#         (indication_key, indication_filter),
#     ]
# )
# newdata = [d for d in data[indication_key] if d is not None]
# for d in newdata:
#     if not d:
# print(data[indication_key][0])
# print(len(data[indication_key]))
# none_list = []
# for d in newdata:
#     if d is None:
#         print("d was None")
#         none_list.append(d)
# print("number of nones: ", len(none_list))
# ordered_page = sorted(
#     [d for d in newdata if d.text.strip()],
#     key=lambda x: (x.get("y0")),
#     reverse=True,
# )
# ordered_page = sorted(
#     [
#         d
#         for d in data["box_vert"] + data["box_hori"] + data["line_hori"]
#         if d.text.strip()
#     ],
#     key=lambda x: (x.get("y0")),
#     reverse=True,
# )
# for i, line in enumerate(ordered_page):
#     print("{}: {}, {}".format(i, line.get("index"), line.text))


# text_elements = pdf.pq("LTTextLineHorizontal")


# print(data["pagedata"])

# for ix, pn in enumerate(sorted([d for d in data['product_name'] if d.text.strip()], key=lambda x: x.get('y0'), reverse=True)):

# page_count = len(pdf._pages)
# for pg in range(4):
# data = pdf.extract(
#     [("with_parent", 'LTPage[pageid="{}"]'.format(pg)), ("with_formatter", None)]
# )
# indications_header = pdf1.pq(
#     'LTTextLineHorizontal :contains("Therapeutic indications")'
# )
# x0 = float(indications_header.attr("x0"))
# x0 = 70.931  # the margin
# y0 = float(indications_header.attr("y0"))
# print("x0: {}, y0: {}".format(x0, y0))
# indications = pdf1.pq(
#     'LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (70.931, 404.997, 331.396, y0)
# ).text()

# x0, y0 - 30, x0 + 150, y0
# print(indications_header)
# print(indications)
