def get_xpath(element):
    """
    Mimics the JavaScript getXPath function.
    If the element has an id attribute, return an XPath using that id.
    Otherwise, build the XPath by traversing up the parent chain.
    """
    if element is None or not hasattr(element, "tag"):
        return ""

    # If the element has an id, return an XPath based on it.
    id_attr = element.get("id")
    if id_attr:
        return "//*[@id='%s']" % id_attr

    parts = []
    while element is not None and element.tag is not None:
        parent = element.getparent()
        if parent is not None:
            # Find all siblings of the same tag.
            siblings = parent.findall(element.tag)
            # Determine the index (1-based) among siblings.
            index = siblings.index(element) + 1
        else:
            index = 1
        parts.insert(0, "{}[{}]".format(element.tag.lower(), index))
        element = parent

    return "/" + "/".join(parts)


def remove_style_attributes(element):
    """
    Removes the "style" attribute from the element and all its descendants.
    """
    if "style" in element.attrib:
        del element.attrib["style"]
    for child in element.iterdescendants():
        if "style" in child.attrib:
            del child.attrib["style"]
