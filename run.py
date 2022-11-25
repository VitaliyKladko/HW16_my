import json

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# конфигурация для подключения к БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hw_16.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# создаем еще один объект(экземпляр SQLAlchemy), под названеим ДБ и прокидываем в него app
db = SQLAlchemy(app)
# все действия с базой, вне вьюшек, не будут вызывать ошибку
app.app_context().push()

USERS_JSON_PATH = 'data/users.json'
ORDERS_JSON_PATH = 'data/orders.json'
OFFERS_JSON_PATH = 'data/offers.json'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    age = db.Column(db.Integer)
    email = db.Column(db.String)
    role = db.Column(db.String)
    phone = db.Column(db.String)

    def return_data(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
        }


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    start_date = db.Column(db.String)
    end_date = db.Column(db.String)
    address = db.Column(db.String)
    price = db.Column(db.Integer)

    customer_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'))
    executor_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'))

    customer = db.relationship('User', foreign_keys=[customer_id])
    executor = db.relationship('User', foreign_keys=[executor_id])


class Offer(db.Model):
    __tablename__ = 'offer'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(f'{Order.__tablename__}.id'))
    executor_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'))
    order = db.relationship('Order')
    executor = db.relationship('User')


with db.session.begin():
    db.drop_all()
    db.create_all()

    # заполняем таблицу "users" в БД из "data/users.json"
    with open(USERS_JSON_PATH, 'r', encoding='utf-8') as file:
        users_list = json.load(file)

    for i in range(len(users_list)):
        user = User(
            id=users_list[i]['id'],
            first_name=users_list[i]['first_name'],
            last_name=users_list[i]['last_name'],
            age=users_list[i]['age'],
            email=users_list[i]['email'],
            role=users_list[i]['role'],
            phone=users_list[i]['phone'],
        )
        db.session.add(user)

    # Заполняем таблицу order в БД из JSON
    with open(ORDERS_JSON_PATH, 'r', encoding='utf-8') as file:
        order_list = json.load(file)

        for i in range(len(order_list)):
            order = Order(
                id=order_list[i]['id'],
                name=order_list[i]['name'],
                description=order_list[i]['description'],
                start_date=order_list[i]['start_date'],
                end_date=order_list[i]['end_date'],
                address=order_list[i]['address'],
                price=order_list[i]['price'],
                customer_id=order_list[i]['customer_id'],
                executor_id=order_list[i]['executor_id'],
            )
            db.session.add(order)

    # Заполняем таблицу offer в БД из JSON
    with open(OFFERS_JSON_PATH, 'r', encoding='utf-8') as file:
        offer_list = json.load(file)

        for i in range(len(offer_list)):
            offer = Offer(
                id=offer_list[i]['id'],
                order_id=offer_list[i]['order_id'],
                executor_id=offer_list[i]['executor_id']
            )
            db.session.add(offer)


@app.route('/', methods=['GET'])
def main_page():
    return jsonify('homework #16')


@app.route('/users/', methods=['GET', 'POST'])
def get_all_users():

    if request.method == 'GET':
        users = db.session.query(User).all()
        result = []

        for use in users:
            result.append(use.return_data())
        return jsonify(result)

    if request.method == 'POST':
        post_user = request.json
        new_user = User(
            age=post_user['age'],
            email=post_user['email'],
            first_name=post_user['first_name'],
            last_name=post_user['last_name'],
            phone=post_user['phone'],
            role=post_user['role'],

        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify('Ok')


@app.route('/users/<int:user_id>', methods=['GET', 'DELETE', 'PUT'])
def get_user_by_id(user_id):

    if request.method == 'GET':
        user = db.session.query(User).get(user_id)
        return jsonify(
            {
                "id": user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'age': user.age,
                'email': user.email,
                'role': user.role,
                'phone': user.phone,
            }
        )

    if request.method == 'DELETE':
        db.session.query(User).filter(User.id == user_id).delete()
        db.session.commit()
        return jsonify(f'User #{user_id} is delete')

    if request.method == 'PUT':
        post_values = request.json
        user_to_update = db.session.query(User).get(user_id)

        required_fields = ['id', 'first_name', 'last_name', 'age', 'email', 'role', 'phone']

        for field in required_fields:
            if field not in post_values:
                return jsonify(f'Поле "{field}" не заполнено')

        user_to_update.id = post_values['id']
        user_to_update.first_name = post_values['first_name']
        user_to_update.last_name = post_values['last_name']
        user_to_update.age = post_values['age']
        user_to_update.email = post_values['email']
        user_to_update.role = post_values['role']
        user_to_update.phone = post_values['phone']

        db.session.commit()
        return jsonify(f'User # {user_id} is update')


@app.route('/orders/', methods=['GET', 'POST'])
def get_all_orders():

    if request.method == 'GET':
        orders = db.session.query(Order).all()
        result = []

        for order in orders:
            result.append(
                {
                    'id': order.id,
                    'name': order.name,
                    'description': order.description,
                    'start_date': order.start_date,
                    'end_date': order.end_date,
                    'address': order.address,
                    'price': order.price,
                    'customer_id': order.customer_id,
                    'executor_id': order.executor_id,
                }
            )
        return jsonify(result)

    if request.method == 'POST':
        post_order = request.json
        new_order = Order(
                id=post_order['id'],
                name=post_order['name'],
                description=post_order['description'],
                start_date=post_order['start_date'],
                end_date=post_order['end_date'],
                address=post_order['address'],
                price=post_order['price'],
                customer_id=post_order['customer_id'],
                executor_id=post_order['executor_id']
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify('Ok, new order is add')


@app.route('/orders/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
def get_order_by_id(order_id):

    if request.method == 'GET':
        order = db.session.query(Order).get(order_id)
        return jsonify(
            {
                'id': order.id,
                'name': order.name,
                'description': order.description,
                'start_date': order.start_date,
                'end_date': order.end_date,
                'address': order.address,
                'price': order.price,
                'customer_id': order.customer_id,
                'executor_id': order.executor_id,
            }
        )

    if request.method == 'DELETE':
        order_to_delete = db.session.query(Order).get(order_id)
        db.session.delete(order_to_delete)
        db.session.commit()
        return jsonify(f'Order # {order_id} is delete')

    if request.method == 'PUT':
        update_data = request.json
        order_to_up = db.session.query(Order).get(order_id)

        order_to_up.id = update_data['id']
        order_to_up.name = update_data['name']
        order_to_up.description = update_data['description']
        order_to_up.start_date = update_data['start_date']
        order_to_up.end_date = update_data['end_date']
        order_to_up.address = update_data['address']
        order_to_up.price = update_data['price']
        order_to_up.customer_id = update_data['customer_id']
        order_to_up.executor_id = update_data['executor_id']
        db.session.commit()

        return jsonify(f'Order #{order_id} is update')


@app.route('/offers/', methods=['GET', 'POST'])
def get_all_offers():

    if request.method == 'GET':
        offers = db.session.query(Offer).all()
        result = []

        for offer in offers:
            result.append(
                {
                    'id': offer.id,
                    'order_id': offer.order_id,
                    'executor_id': offer.executor_id,
                }
            )
        return jsonify(result)

    if request.method == 'POST':
        new_offer_data = request.json
        new_offer = Offer(
            id=new_offer_data['id'],
            order_id=new_offer_data['order_id'],
            executor_id=new_offer_data['executor_id']
        )
        db.session.add(new_offer)
        db.session.commit()

        return jsonify(f'New offer is add')


@app.route('/offers/<int:offer_id>', methods=['GET', 'DELETE', 'PUT'])
def get_offer_by_id(offer_id):

    if request.method == 'GET':
        offer = db.session.query(Offer).get(offer_id)
        return jsonify(
            {
                'id': offer.id,
                'order_id': offer.order_id,
                'executor_id': offer.executor_id,
            }
        )

    if request.method == 'PUT':
        offer_data = request.json
        offer_to_up = db.session.query(Offer).get(offer_id)

        offer_to_up.id = offer_data['id']
        offer_to_up.order_id = offer_data['order_id']
        offer_to_up.executor_id = offer_data['executor_id']
        db.session.commit()
        return jsonify(f'Offer #{offer_id} is update')

    if request.method == 'DELETE':
        offer_to_delete = db.session.query(Offer).get(offer_id)
        db.session.delete(offer_to_delete)
        db.session.commit()
        return jsonify(f'Offer #{offer_id} delete')


if __name__ == '__main__':
    app.run(debug=True)
