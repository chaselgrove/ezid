def xml_add_text(doc, tag, value):
    elements = doc.getElementsByTagName(tag)
    assert len(elements) == 1
    elements[0].appendChild(doc.createTextNode(value))
    return

def xml_text(el):
    data = ''
    for cn in el.childNodes:
        if cn.nodeType == cn.TEXT_NODE:
            data += cn.data
    return data

# eof
