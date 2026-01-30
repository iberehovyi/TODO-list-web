from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean, DateTime
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#User management object
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    lists = relationship("Lists", back_populates="user")

class Lists(db.Model):
    __tablename__ = "lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #relationship to User
    user = relationship("User", back_populates="lists")
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    tasks = relationship("Task", back_populates="list")
    # body of list
    date_created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

class Task(db.Model):
    __tablename__ = "tasks"
    # relationship to List
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('lists.id'))
    list = relationship("Lists", back_populates="tasks")
    # body of task
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

with app.app_context():
    db.create_all()

@app.route("/login", methods=["GET", "POST"])
def login():
    is_logged_in = current_user.is_authenticated
    data = request.form
    if request.method == "POST":
        user = db.session.execute(db.select(User).where(User.user_name == data["name"])).scalar()
        if not user:
            flash("That nickname does not exist, please try again.")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, data["password"]):
            flash('Password incorrect, please try again.')
            return redirect(url_for("login"))
        else:
            login_user(user)
        return redirect(url_for("home"))
    return render_template("login.html", is_logged=is_logged_in)

@app.route("/register", methods=["GET", "POST"])
def register():
    is_logged_in = current_user.is_authenticated
    data = request.form
    if request.method == "POST":
        hashedpass = generate_password_hash(
            password=data["password"],
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            user_name=data["name"],
            password=hashedpass
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", is_logged=is_logged_in)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/', methods=["GET", "POST"])
def home():
    curr_user = current_user
    is_logged_in = curr_user.is_authenticated
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    print(current_user.user_name)
    lists_get = db.session.execute(db.select(Lists).where(Lists.user_id == current_user.id).order_by(Lists.id.desc())).scalars().all()
    if request.method == 'POST':
        # Move these two lines INSIDE the if block
        data = request.form
        new_list = Lists(
            user_id=current_user.id,
            name=data['list_name'],
            description=data['list_description']
        )
        db.session.add(new_list)
        db.session.commit()
        return redirect(url_for("selected_list", list_id=new_list.id))
    return render_template("index.html", lists=lists_get, is_logged=is_logged_in, user=curr_user)

@app.route("/list/<int:list_id>", methods=["GET", "POST"])
def selected_list(list_id):
    curr_user = current_user
    is_logged_in = curr_user.is_authenticated
    lists_get = db.session.execute(db.select(Lists).where(Lists.user_id == current_user.id)).scalars().all()
    current_list = db.session.execute(db.select(Lists).where(Lists.id == list_id)).scalar()
    if current_list.user_id != current_user.id:
        return redirect(url_for("home"))
    tasks_get = db.session.execute(db.select(Task).where(Task.list_id == list_id).order_by(Task.is_completed.asc(), Task.id.desc())).scalars().all()
    data = request.form
    if request.method == 'POST':
        if data['task']:
            new_task = Task(
                list_id=list_id,
                task_text=data['task'],
                priority=int(data['priority']),
            )
            print(f"Adding Task: {new_task.task_text} on {new_task.date}")
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("selected_list", list_id=list_id))
    return render_template("selected-list.html", tasks=tasks_get, list_id=list_id, all_lists=lists_get, current_list=current_list, is_logged=is_logged_in, user=curr_user)

@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task_to_update = db.get_or_404(Task, task_id)
    # Toggle the status of task
    task_to_update.is_completed = not task_to_update.is_completed
    db.session.commit()
    return redirect(url_for("selected_list", list_id=task_to_update.list_id))

@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task_to_delete = db.get_or_404(Task, task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("selected_list", list_id=task_to_delete.list_id))

if __name__ == "__main__":
    app.run(debug=True, port=5002)