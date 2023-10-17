from lxml import etree

class Parser:
    def __init__(self):
        self.parser = etree.XMLParser(remove_comments=True)

    def parse_clothes(self):
        doc = etree.parse("config/inventory/clothes.xml",
                          parser=self.parser)
        root = doc.getroot()
        clths = {'boy': {}, 'girl': {}}
        for element in root.find('category'):
            if element.attrib['gender'] in clths:
                gender = element.attrib['gender']
                for el in element.findall('category'):
                    for item in el.findall('.//item'):
                        clths[gender][item.attrib["id"]] = {}
                        if "logCategory2" in item.getparent().attrib:
                            clths[gender][item.attrib["id"]]["category"] = item.getparent().attrib["logCategory2"]
                        for at in item.attrib:
                            clths[gender][item.attrib["id"]][at] = item.attrib[at]
                            if item.attrib[at].isdigit():
                                clths[gender][item.attrib["id"]][at] = int(item.attrib[at])
        return clths

    def parse_furniture(self):
        furniture = {}
        for filename in ["furniture.xml", "kitchen.xml", "bathroom.xml",
                         "decor.xml", "present.xml", "roomLayout.xml"]:
            doc = etree.parse(f"config/inventory/{filename}",
                              parser=self.parser)
            root = doc.getroot()
            for item in root.findall(".//item"):
                name = item.attrib["id"]
                furniture[name] = {}
                for attr in ["gold", "rating", "silver"]:
                    if attr in item.attrib:
                        furniture[name][attr] = int(item.attrib[attr])
                furniture[name]['slot'] = filename.split('.')[1]
        return furniture

    def parse_craft(self):
        doc = etree.parse("config/modules/craft.xml",
                          parser=self.parser)
        root = doc.getroot()
        items = {}
        for item in root.findall(".//craftedItem"):
            views = None
            id_ = item.attrib["itemId"]
            if 'views' in item.attrib:
                views = item.attrib['views']
            items[id_] = {"items": {}, 'views': views}
            if "craftedId" in item.attrib:
                items[id_]["craftedId"] = item.attrib["craftedId"]
                items[id_]["count"] = int(item.attrib["count"])
            for tmp in item.findall("component"):
                itemId = tmp.attrib["itemId"]
                count = int(tmp.attrib["count"])
                items[id_]["items"][itemId] = count
        return items

    def parse_game_items(self):
        doc = etree.parse("config/inventory/game.xml",
                          parser=self.parser)
        root = doc.getroot()
        items = {}
        for category in root.findall(".//category"):
            cat_name = category.attrib["id"]
            items[cat_name] = {}
            for item in category.findall(".//item"):
                name = item.attrib["id"]
                items[cat_name][name] = {}
                for attr in ["gold", "silver", "saleSilver"]:
                    if attr in item.attrib:
                        items[cat_name][name][attr] = int(item.attrib[attr])
                    else:
                        if attr == "saleSilver":
                            continue
                        items[cat_name][name][attr] = 1
                for attr in ["canBuy"]:
                    if attr in item.attrib:
                        items[cat_name][name][attr] = bool(int(item.attrib[attr]))
                    else:
                        items[cat_name][name][attr] = attr == "canBuy"
        return items

    def parse_relations(self):
        doc = etree.parse("config/modules/relations.xml",
                          parser=self.parser)
        root = doc.getroot()
        statuses = {}
        tmp = root.find(".//statuses")
        for status in tmp.findall("status"):
            id_ = int(status.attrib["id"])
            statuses[id_] = {"transition": [], "progress": {}}
            for progress in status.findall("progress"):
                value = int(progress.attrib["value"])
                tmp_status = int(progress.attrib["status"])
                statuses[id_]["progress"][value] = tmp_status
            for trans in status.findall("statusForTransition"):
                tmp_id = int(trans.attrib["id"])
                statuses[id_]["transition"].append(tmp_id)
        return statuses

    def parse_relation_progresses(self):
        doc = etree.parse("config/modules/relations.xml")
        root = doc.getroot()
        progresses = {}
        tmp = root.find(".//progresses")
        for progress in tmp.findall("progress"):
            value = int(progress.attrib["value"])
            progresses[progress.attrib["reason"]] = value
        return progresses
