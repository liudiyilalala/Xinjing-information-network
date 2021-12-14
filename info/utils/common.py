def do_index_class(index):
    """自定义过滤器，过滤点击排行的class属性"""
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""
