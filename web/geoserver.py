import flask
import const

app: flask.Flask = flask.Flask(__name__)

HOST_NAME: str = "192.168.1.2"
PORT_NUMBER: int = 80

LOCAL: str = "RU"


@app.route('/geoserver/')
def geo_local():
    return LOCAL


@app.route('/geoserver/server', methods=["POST"])
def geo_server():
    return {"server": const.HOST + ":" + str(const.PORT)}


if __name__ == "__main__":
    app.secret_key = 'geoserver@qwikks'
    app.run(host=HOST_NAME, port=PORT_NUMBER)
