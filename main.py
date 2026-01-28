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

class Task(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

with app.app_context():
    db.create_all()
@app.route('/', methods=["GET", "POST"])
def home():
    tasks_get = db.session.execute(db.select(Task).order_by(Task.is_completed.asc(), Task.id.desc())).scalars().all()
    data = request.form
    # time_now = datetime.now().strftime("%d-%m-%Y at %H:%M")
    if request.method == 'POST':
        new_task = Task(
            task_text=data['task'],
            priority=int(data['priority']),
        )
        print(f"Adding Task: {new_task.task_text} on {new_task.date}")
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("index.html", tasks=tasks_get)


@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task_to_update = db.get_or_404(Task, task_id)
    # Toggle the status of task
    task_to_update.is_completed = not task_to_update.is_completed
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port=5002)

time = datetime.now().date()
print(time)