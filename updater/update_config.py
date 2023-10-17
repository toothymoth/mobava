import json, requests, os

def parser():
    with open("project.manifest", "r", encoding="utf-8") as f:
        content = json.loads(f.read())
    mainlink = content["packageUrl"]
    return content, mainlink

def filterToConfig():
    files = []
    content, mainlink = parser()
    for con in content["assets"]:
        if con.split("/")[0] == "config":
            files.append(con)
    return files, mainlink

def _createfolder(folder):
    try:
        os.mkdir(folder)
        return True
    except FileNotFoundError:
        return False

def createFolders(files):
    if not os.path.isdir("config"):
        os.mkdir("config")
    os.chdir("config")
    for file in files:
        folder = "/".join(file.split("/")[1:-1])
        if not folder:
            continue
        if not os.path.isdir(folder):
            i = 0
            while not _createfolder(folder):
                _createfolder(folder.split("/")[i])
                i+=1
                


def main():
    f = os.getcwd()
    files, mainlink = filterToConfig()
    createFolders(files)
    os.chdir(f)
    for file in files:
        with open(file, "wb") as g:
            g.write(requests.get(mainlink+file, verify=False).content)

main()

