import json

from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    order_lines = db.relationship('OrderLine', backref='product', lazy=True)

    def __repr__(self):
        return '<Product %s>' % self.name

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return '<Category %s>' % self.name

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    order_lines = db.relationship('OrderLine', backref='order', lazy=True)

    def __repr__(self):
        return '<Order %s>' % str(self.id)

class OrderLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<OrderLine (%d, %d)>' % (self.order_id, self.product.id)

@app.route('/')
def frontpage():
    categories = Category.query.all()
    categoryIds = []
    for category in categories:
        if category.name in request.args:
            categoryIds.append(category.id)
    
    query = Product.query

    if 'search' in request.args:
        search = '%' + request.args.get('search') + '%'
        query = query.filter(Product.name.like(search))
    
    if len(categoryIds) > 0:
        query = query.filter(Product.category_id.in_(categoryIds))

    products = query.all()

    return render_template('frontpage.html', products=products, categories=categories)

@app.route('/<int:id>')
def detail(id):
    product = Product.query.get_or_404(id)
    return render_template('detail.html', product=product)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/order', methods=['POST'])
def order():
    order = Order(name=request.form['name'], address=request.form['address'], postal_code=request.form['postal_code'],
        city=request.form['city'])

    products = json.loads(request.form['products'])
    for id, detail in products.items():
        product = Product.query.get(id)
        quantity = detail['quantity']
        if(quantity > product.stock):
            return render_template('status.html', success=False)
        product.stock -= quantity
        order_line = OrderLine(product_id=id, quantity=quantity)
        order.order_lines.append(order_line)

    order = db.session.add(order)
    db.session.commit()
    return render_template('status.html', success=True)
