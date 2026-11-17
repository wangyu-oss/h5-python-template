def menu_tree(menus):
    rows = [menu.public() for menu in menus]
    grouped = {}
    for row in rows:
        grouped.setdefault(row['parent_id'], []).append(row)

    def build(parent_id):
        nodes = grouped.get(parent_id, [])
        for node in nodes:
            node['children'] = build(node['id'])
        return nodes

    return build(None)
