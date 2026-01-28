from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean, DateTime

app = Flask(__name__)

bootstrap = Bootstrap5(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Lists(db.Model):
    __tablename__ = "lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    tasks = relationship("Task", back_populates="list")

class Task(db.Model):
    __tablename__ = "tasks"
    # skeleton for relationship
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('lists.id'))
    list = relationship("Lists", back_populates="tasks")
    # body of list
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

with app.app_context():
    db.create_all()
    # existing_list = db.session.execute(db.select(Lists).where(Lists.name == 'List test #1')).scalar()
    #
    # if not existing_list:
    #     listadd = Lists(name='List test #1')
    #     db.session.add(listadd)
    #     db.session.commit()
    #     print("Initial list created!")

@app.route('/', methods=["GET", "POST"])
def home():
    lists_get = db.session.execute(db.select(Lists).order_by(Lists.id.desc())).scalars().all()

    if request.method == 'POST':
        # Move these two lines INSIDE the if block
        data = request.form
        new_list = Lists(
            name=data['list_name'],
            # description=data.get('list_description')
        )
        db.session.add(new_list)
        db.session.commit()
        return redirect(url_for("selected_list", list_id=new_list.id))

    return render_template("index.html", lists=lists_get)

@app.route("/list/<int:list_id>", methods=["GET", "POST"])
def selected_list(list_id):
    tasks_get = db.session.execute(db.select(Task).where(Task.list_id == list_id).order_by(Task.is_completed.asc(), Task.id.desc())).scalars().all()
    lists_get = db.session.execute(db.select(Lists)).scalars().all()
    current_list_name = db.session.execute(db.select(Lists).where(Lists.id == list_id)).scalar()
    data = request.form
    # time_now = datetime.now().strftime("%d-%m-%Y at %H:%M")
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
    return render_template("selected-list.html", tasks=tasks_get, list_id=list_id, all_lists=lists_get, current_list=current_list_name)

@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task_to_update = db.get_or_404(Task, task_id)

    # Toggle the status of task
    task_to_update.is_completed = not task_to_update.is_completed
    db.session.commit()
    return redirect(url_for("selected_list", list_id=task_to_update.list_id))

##TODO
# @app.route("/complete/<int:task_id>")
# def create_list(task_id):
#     task_to_update = db.get_or_404(Task, task_id)
#
#     # Toggle the status of task
#     task_to_update.is_completed = not task_to_update.is_completed
#     db.session.commit()
#     return redirect(url_for("selected_list", list_id=task_to_update.list_id))

if __name__ == "__main__":
    app.run(debug=True, port=5002)

time = datetime.now().date()
print(time)