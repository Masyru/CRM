from flask import Flask, request, render_template, send_from_directory
from json import dumps
from pandas import DataFrame, ExcelWriter
from database import *
from logging import basicConfig, DEBUG, getLogger
from logging.handlers import RotatingFileHandler
from datetime import datetime
from os import getcwd


def time_calculation(obj: dict, time_is_now):
    if obj and obj["date_of_creation"]:
        obj["date_of_creation"] = (time_is_now - obj["date_of_creation"]) // 86400
    return obj["date_of_creation"]


def preparation_request(request_for_preparation):
    new_request = {
        "program_name": request_for_preparation[2] if len(request_for_preparation) > 2 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "country": request_for_preparation[3] if len(request_for_preparation) > 3 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "status": request_for_preparation[4] if len(request_for_preparation) > 4 else
        logger.warning("WARNING] - In history_table is not fully filled request"),
        "type": request_for_preparation[5] if len(request_for_preparation) > 5 else
        logger.warning("WARNING] - In history_table is not fully filled request"),
        "departure_date": request_for_preparation[6] if len(request_for_preparation) > 6 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "date_of_creation": request_for_preparation[7] if len(request_for_preparation) > 7 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "user_commit": request_for_preparation[8] if len(request_for_preparation) > 8 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "money": request_for_preparation[9] if len(request_for_preparation) > 9 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "cause": request_for_preparation[10] if len(request_for_preparation) > 10 else
        logger.warning("[WARNING] - In history_table is not fully filled request"),
        "brief": request_for_preparation[11] if len(request_for_preparation) > 11 else
        logger.warning("[WARNING] - In history_table is not fully filled request")
    }
    return new_request


def preparation_of_client_data(client, time_is_now):
    parents = parents_table.get(client[0])
    if not parents:
        parents = [None] * 10

    client = {
        "client_id": client[0],
        "client_name": client[1],
        "date_of_birth": client[2],
        "phone_number": client[3],
        "mail": client[4],
        "client_status": client[5],
        "date_of_creation": client[6],
        "parents": {
            "first_parent": {
                "name": parents[2],
                "phone_number": parents[3],
                "email": parents[4],
                "work": parents[5]
            },
            "second_parent": {
                "name": parents[6],
                "phone_number": parents[7],
                "email": parents[8],
                "work": parents[9]
            }
        }
    }
    client["date_of_creation"] = time_calculation(client, time_is_now)

    current_request = current_requests_table.get(client["client_id"])
    if not current_request:
        current_request = [None] * 9
    else:
        current_request = list(current_request)
        current_request[6] = float(time_is_now) - float(current_request[6])
    current_request = {
        "program_name": current_request[2],
        "country": current_request[3],
        "status": current_request[8],
        "type": current_request[4],
        "departure_date": current_request[5],
        "date_of_creation": current_request[6],
        "comment": current_request[7]
    }

    client_history = list(map(preparation_request, history_table.get_all_client_applications(client["client_id"])))
    history_data = []
    for history in client_history:
        history["date_of_creation"] = time_calculation(history, time_is_now)
        history_data.append(history)

    client_data = {
        "client": client,
        "request": current_request,
        "history": history_data
    }

    return client_data


def log_connect_table(table):
    if table.get_error() == "-1":
        logger.info(f"[INFO] - {table.__class__.__name__} connected to the database")
        return 0
    logger.info(f"[FAILED] - {table.__class__.__name__} could not connect to the database")
    return 1


app = Flask(__name__, template_folder="./frontend", static_folder="./frontend")


@app.route('/', methods=["GET"])
def main_page():
    logger.warning(f"[WARNING] - Access to the site from {request.environ['REMOTE_ADDR']}")
    return render_template("index.html")


@app.route("/Entry", methods=["POST"])
def entry():
    data = request.json

    if list(data.keys()) != ["login", "password"]:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    response = admins_table.check_password(data["login"], data["password"])
    logger.info("[OK] - Entry")
    return dumps(response)


@app.route("/UserData", methods=["POST"])
def user_data():
    data = request.json

    if list(data.keys()) != ['name', 'status', 'date_of_birth', 'number', 'mail', 'firstParent', 'secondParent']:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    client_id = clients_table.get_client_id(data["name"], data["date_of_birth"])
    if client_id:
        logger.info("[FAILED] - User already exists")
        return dumps(client_id[0])

    first_parent = data["firstParent"]
    second_parent = data["secondParent"]

    if not (first_parent or second_parent):
        logger.info("[FAILED] - Missing parents data")
        return dumps(None)

    if not first_parent:
        first_parent["name"] = None
        first_parent["number"] = None
        first_parent["mail"] = None
        first_parent["job"] = None

    if not second_parent:
        second_parent["name"] = None
        second_parent["number"] = None
        second_parent["mail"] = None
        second_parent["job"] = None

    if list(first_parent.keys()) != ["name", "number", "mail", "job"] or \
            list(second_parent.keys()) != ["name", "number", "mail", "job"]:
        logger.warning("[WARNING] - Invalid parents data")
        return dumps(None)

    clients_table.insert(data["name"], data["date_of_birth"], data["number"], data["mail"],
                         1 if data["status"] == "Новый" else
                         2 if data["status"] == "Повторный" else
                         3 if data["status"] == "V.I.P." else 0)
    logger.info("[OK] - User created")

    client_id = clients_table.get_client_id(data["name"], data["date_of_birth"])[0]

    parents_table.insert(
        client_id,
        first_parent["name"] if first_parent["name"] else None,
        first_parent["number"] if first_parent["number"] else None,
        first_parent["mail"] if first_parent["mail"] else None,
        first_parent["job"] if first_parent["job"] else None,
        second_parent["name"] if second_parent["name"] else None,
        second_parent["number"] if second_parent["number"] else None,
        second_parent["mail"] if second_parent["mail"] else None,
        second_parent["job"] if second_parent["job"] else None
    )
    logger.info("[OK] - User’s parents are recorded")
    return dumps(client_id)


@app.route("/ChangeClient", methods=["POST"])
def change_client():
    data = request.json
    if list(data.keys()) != ["token", "client"]:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    new_client_data = data["client"]
    if list(new_client_data.keys()) != ["id", "name", "date_of_birth",
                                        "mail", "phone_number",
                                        "first_parent", "second_parent"]:
        logger.warning("[WARNING] - Invalid client data")
        return dumps(None)

    elif list(new_client_data["first_parent"].keys()) != ["name", "number", "mail", "job"]:
        logger.warning("[WARNING] - Invalid first parent data")
        return dumps(None)

    elif list(new_client_data["second_parent"].keys()) != ["name", "number", "mail", "job"]:
        logger.warning("[WARNING] - Invalid second parent data")
        return dumps(None)

    check = admins_table.check_access(data["token"])
    if check != 1:
        if check == -1:
            logger.warning("[WARNING] - Token failed verification")
        else:
            logger.info("[FAILED] - Token does not have access ")
        return dumps(None)

    if not clients_table.change(new_client_data["id"], new_client_data["name"],
                                new_client_data["date_of_birth"], new_client_data["mail"],
                                new_client_data["phone_number"], new_client_data["first_parent"],
                                new_client_data["second_parent"], parents_table):
        return dumps(None)
    logger.info("[INFO] - ChangeClient")
    return dumps("Changed")


@app.route("/ChangeCurrent", methods=["POST"])
def change_current():
    data = request.json
    if list(data.keys()) != ["token", "status", "name_of_program", "country",
                             "type_of_program", "comment", "id", "date_of_will_fly"]:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    client_id = data["id"]

    if not clients_table.get(client_id):
        logger.warning("[WARNING] - User does not exist")
        return dumps(None)

    check = admins_table.check_access(data["token"])

    if check != 1:
        if check == -1:
            logger.warning("[WARNING] - Token failed verification")
        else:
            logger.info("[FAILED] - Token does not have access")
        return dumps(None)

    current_requests_table.change(client_id, data["name_of_program"],
                                  data["country"], data["type_of_program"],
                                  data["date_of_will_fly"], data["comment"])
    logger.info("[OK] - Application changed")
    return dumps("I hacked your system again")


@app.route("/ChangeCurrentStatus", methods=["POST"])
def change_current_status():
    global is_closed_application_file, is_refused_application_file

    data = request.json
    if list(data.keys()) != ["token", "status", "data"] and list(data.keys()) != ['data', 'token', 'status']:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    client_id = data["data"]["id"]

    if not clients_table.get(client_id):
        logger.warning("[WARNING] - User does not exist")
        return dumps(None)

    check = admins_table.check_access(data["token"])

    if check == -1:
        logger.warning("[WARNING] - Token failed verification")
        return dumps(None)

    if data["status"] == "Закрыто":
        count = history_table.get_count_closed_client_applications(client_id)
        if count == 0:
            clients_table.set_client_status(client_id, 2)
        elif count == 1:
            clients_table.set_client_status(client_id, 3)

        current_request = current_requests_table.pop(client_id)
        history_table.insert(client_id=current_request[1],
                             program_name=current_request[2],
                             country=current_request[3],
                             program_type=current_request[4],
                             departure_date=current_request[5],
                             date_of_creation=current_request[6],
                             commit=current_request[7],
                             status=7, money=data["data"]["money"],
                             brief=data["data"]["brief"])
        is_closed_application_file = False

    elif data["status"] == "Отказ":
        current_request = current_requests_table.pop(client_id)
        history_table.insert(
            client_id=current_request[1],
            program_name=current_request[2],
            country=current_request[3],
            program_type=current_request[4],
            departure_date=current_request[5],
            date_of_creation=current_request[6],
            commit=current_request[7],
            status=8, cause=data["data"]["cause"], brief=data["data"]["brief"])
        is_refused_application_file = False
    else:
        current_requests_table.set_status(client_id,
                                          1 if data["status"] == "Заявка" else
                                          2 if data["status"] == "Договор" else
                                          3 if data["status"] == "Оплата" else
                                          4 if data["status"] == "Выезд" else
                                          5 if data["status"] == "Консультирование" else
                                          6 if data["status"] == "Оформление" else 0)
    logger.info("[OK] - Application changed")
    return dumps("I hacked your system again")


@app.route("/UserRequest", methods=["POST"])
def user_request():
    global is_current_application_file

    data = request.json

    if list(data.keys()) != ["name_of_program", "status", "country",
                             "date_of_will_fly", "comment", "type_of_program", "id"]:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    client_id = data["id"]

    if not clients_table.get(client_id):
        logger.warning("[WARNING] - User does not exist")
        return dumps(None)

    elif current_requests_table.get(client_id):
        logger.warning("[WARNING] - User already has an open application")
        return dumps(None)
    status = data["status"]
    current_requests_table.insert(client_id, data["name_of_program"],
                                  data["country"], data["type_of_program"],
                                  data["date_of_will_fly"], data["comment"],
                                  1 if status == "Заявка" else
                                  2 if status == "Договор" else
                                  3 if status == "Оплата" else
                                  4 if status == "Выезд" else
                                  5 if status == "Консультирование" else
                                  6 if status == "Оформлемние" else
                                  7 if status == "Закрыто" else
                                  8 if status == "Отказ" else 0)
    is_current_application_file = False
    logger.info("[OK] - Application is recorded")
    return dumps("I hacked your system")


@app.route("/GetInfo", methods=["GET"])
def get_info():
    time_is_now = time()
    response = []

    for client in clients_table.get_all():
        response.append(preparation_of_client_data(client, time_is_now))
    logger.info("[OK] - GetInfo")
    return dumps(response)


@app.route("/Search", methods=["POST"])
def search():
    data = request.json
    logger.info(f"[INFO] - Search data: {data}")
    if list(data.keys()) != ["searchLine", "phone_number", "status"]:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)
    time_is_now = time()
    phone = data["phone_number"]
    line = data["searchLine"].split()
    status = data["status"]
    status = 1 if status == "Заявка" else \
        2 if status == "Договор" else \
        3 if status == "Оплата" else \
        4 if status == "Выезд" else \
        5 if status == "Консультирование" else \
        6 if status == "Оформление" else \
        7 if status == "Закрыто" else \
        8 if status == "Отказ" else 0

    line_f = "lambda x:"
    if len(line) > 1:
        line_f += f"x[1].lower() == \"{' '.join(line).lower()}\""
    else:
        line_f += f"\"{' '.join(line).lower()}\" in x[1].lower()"

    if phone:
        if len(line_f) > 9:
            line_f += " and "

        if phone == '+7':
            line_f += "True"

        elif len(phone) == 12:
            line_f += f"x[3] == \"{phone}\""

        else:
            line_f += f"\"{phone}\" in x[3]"

    if line_f == 9:
        logger.info("[FAILED] - Empty search query")
        return dumps(None)

    f = eval(line_f)
    res = clients_table.get_all()
    res = list(filter(f, res))
    response = []

    for client in res:
        response.append(preparation_of_client_data(client, time_is_now))
    if status:
        response = list(filter(
            lambda x: x['request']['status'] == status if status else lambda y: True,
            response
        ))
    logger.info("[INFO] - "
                f"Number of coincidences: {len(response)}")
    logger.info("[OK] - Search completed")
    return dumps(response)


@app.route("/Delete/Client", methods=["POST"])
def delete():
    data = request.json

    if list(data.keys()) != ["token", "client_id"]:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    check = admins_table.check_access(data["token"])

    if check != 1:
        if check == -1:
            logger.warning("[WARNING] - Token failed verification")
        else:
            logger.info("[FAILED] - Token does not have access")
        return dumps(None)

    clients_table.delete(data["client_id"])
    logger.info("[OK] - Client deleted")
    return dumps("sudo rm -rf /client/")


@app.route("/Download/<path:token>/finance.xlsx", methods=["GET"])
def download_closed(token):
    global is_closed_application_file

    if len(token) != 16:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    check = admins_table.check_access(token)

    if check == -1:
        return dumps("Permission denied")

    applications = history_table.get_finance_applications()
    data_for_excel = {
        "ФИО клиента": [],
        "Программа": [],
        "Страна": [],
        "Статус": [],
        "Тип": [],
        "Дата выезда": [],
        "Комментарий": [],
        "Контакты": [],
    }
    if check == 1:
        data_for_excel["Выручка"] = []

    for application in applications:
        client = clients_table.get(application[1])

        data_for_excel["ФИО клиента"].append(client[1] if client else "")
        data_for_excel["Программа"].append(application[2])
        data_for_excel["Страна"].append(application[3])
        data_for_excel["Статус"].append(
            "Заявка" if application[4] == 1 else
            "Договор" if application[4] == 2 else
            "Оплата" if application[4] == 3 else
            "Выезд" if application[4] == 4 else
            "Консультирование" if application[4] == 5 else
            "Оформление" if application[4] == 6 else
            "Закрыто" if application[4] == 7 else
            "Отказ" if application[4] == 8 else "Не заполнен"
        )
        data_for_excel["Тип"].append(application[5])
        data_for_excel["Дата выезда"].append(application[6])
        comment, contacts = application[7].split("--Contacts--")
        data_for_excel["Комментарий"].append(comment)
        data_for_excel["Контакты"].append(contacts)
        if check == 1:
            data_for_excel["Выручка"].append(application[8])

        df = DataFrame(data_for_excel)
        writer = ExcelWriter("Main/excel/closed_applications.xlsx")
        df.to_excel(writer, "Closed", index=False)
        writer.save()
        is_closed_application_file = True

    logger.info("[OK] - Closed file sent")
    return send_from_directory("Main/excel", filename="closed_applications.xlsx")


@app.route("/Download/<path:token>/closed.xlsx", methods=["GET"])
def download_refused(token):
    global is_refused_application_file

    if len(token) != 16:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    check = admins_table.check_access(token)

    if check != 1:
        if check == -1:
            logger.warning("[WARNING] - Token failed verification")
        else:
            logger.info("[FAILED] - Token does not have access")
        return dumps(None)

    logger.info(getcwd())
    if not is_refused_application_file:

        data_for_excel = {
            "ФИО клиента": [],
            "Программа": [],
            "Страна": [],
            "Статус": [],
            "Тип": [],
            "Дата выезда": [],
            "Комментарий": [],
            "Контакты": [],
            "Краткая причина": [],
            "Причина": []
        }
        applications = history_table.get_closed_applications()
        for i, application in enumerate(applications):
            client = clients_table.get(application[1])
            if client:
                applications[i] += (client[1],)
            else:
                applications[i] += ("",)

            data_for_excel["ФИО клиента"].append(client[1] if client else "")
            data_for_excel["Программа"].append(application[2])
            data_for_excel["Страна"].append(application[3])
            data_for_excel["Статус"].append(
                "Заявка" if application[4] == 1 else
                "Договор" if application[4] == 2 else
                "Оплата" if application[4] == 3 else
                "Выезд" if application[4] == 4 else
                "Консультирование" if application[4] == 5 else
                "Оформление" if application[4] == 6 else
                "Закрыто" if application[4] == 7 else
                "Отказ" if application[4] == 8 else "Не заполнен"
            )
            data_for_excel["Тип"].append(application[5])
            data_for_excel["Дата выезда"].append(application[6])
            comment, contacts = application[7].split("--Contacts--")
            data_for_excel["Комментарий"].append(comment)
            data_for_excel["Контакты"].append(contacts)
            data_for_excel["Краткая причина"].append(application[8])
            data_for_excel["Причина"].append(application[9])

        df = DataFrame(data_for_excel)
        writer = ExcelWriter("Main/excel/refused_applications.xlsx")
        df.to_excel(writer, "Refused", index=False)
        writer.save()
        is_refused_application_file = True

    logger.info("[OK] - Refused file sent")
    return send_from_directory("Main/excel", "refused_applications.xlsx")


@app.route("/Download/<path:token>/general.xlsx", methods=["GET"])
def download_general(token):
    global is_current_application_file

    if len(token) != 16:
        logger.warning("[WARNING] - Invalid request data")
        return dumps(None)

    check = admins_table.check_access(token)

    if check != 1:
        if check == -1:
            logger.warning("[WARNING] - Token failed verification")
        else:
            logger.info("[FAILED] - Token does not have access")
        return dumps(None)

    logger.info(getcwd())
    if not is_current_application_file:
        data_for_excel = {
            "ФИО клиента": [],
            "Дата рождения": [],
            "Телефон": [],
            "Email": [],
            "Программа": [],
            "Страна": [],
            "Статус": [],
            "Тип": [],
            "Дата выезда": [],
            "Дата создания": [],
            "Комментарий": [],
            "Контакты": []
        }
        currents = current_requests_table.get_all()

        for current in currents:
            user = clients_table.get(current[1])

            data_for_excel["ФИО клиента"].append(user[1] if user else "")
            data_for_excel["Дата рождения"].append(user[2] if user else "")
            data_for_excel["Телефон"].append(user[3] if user else "")
            data_for_excel["Email"].append(user[4] if user else "")
            data_for_excel["Программа"].append(current[2])
            data_for_excel["Страна"].append(current[3])
            data_for_excel["Статус"].append(
                "Заявка" if current[8] == 1 else
                "Договор" if current[8] == 2 else
                "Оплата" if current[8] == 3 else
                "Выезд" if current[8] == 4 else
                "Консультирование" if current[8] == 5 else
                "Оформление" if current[8] == 6 else
                "Закрыто" if current[8] == 7 else
                "Отказ" if current[8] == 8 else "Не заполнен"
            )
            data_for_excel["Тип"].append(current[4])
            data_for_excel["Дата выезда"].append(current[5])
            data_for_excel["Дата создания"].append(datetime.fromtimestamp(current[6]))
            comment, contacts = current[7].split("--Contacts--")
            data_for_excel["Комментарий"].append(comment)
            data_for_excel["Контакты"].append(contacts)

        df = DataFrame(data_for_excel)
        writer = ExcelWriter("Main/excel/current_applications.xlsx")
        df.to_excel(writer, "Current", index=False)
        writer.save()
        is_current_application_file = True

    logger.info("[OK] - Current file sent")
    return send_from_directory("Main/excel", "current_applications.xlsx")


# TODO: сделать удаление токенов
@app.route("/Exit", methods=["POST"])
def end():
    pass


basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=DEBUG, filename=u'log.log')
handler = RotatingFileHandler('log.log', maxBytes=1024 * 1024 * 100)
logger = getLogger('init')

is_closed_application_file = False
is_refused_application_file = False
is_current_application_file = False
total_error = 0

db = DB("database")
logger.info(f"[OK] - Created or opened database | Name {db.name}")

admins_table = AdminsTable(db.get_connection())
total_error += log_connect_table(admins_table)

clients_table = ClientsTable(db.get_connection())
total_error += log_connect_table(clients_table)

parents_table = ParentsTable(db.get_connection())
total_error += log_connect_table(parents_table)

history_table = HistoryTable(db.get_connection())
total_error += log_connect_table(history_table)

current_requests_table = CurrentRequestsTable(db.get_connection())
total_error += log_connect_table(current_requests_table)

admins_table.init_table()
clients_table.init_table()
parents_table.init_table()
history_table.init_table()
current_requests_table.init_table()

if __name__ == "__main__":
    app.run(port=8000, host="127.0.0.1")
