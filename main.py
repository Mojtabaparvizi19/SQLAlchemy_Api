from flask import Flask, redirect, request, render_template, url_for
from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer

import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-record.db"

database = SQLAlchemy(model_class=Base)
database.init_app(app=app)


class MovieRecord(database.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(200), nullable=True)
    img_url: Mapped[str] = mapped_column(String(100), nullable=False)


# CREATE TABLE
with app.app_context():
    database.create_all()
headers = {
     "Authorization": "Bearer *****************"
                      ".8******************************************************************"
                      "*********************************************************************Q"
                      ".**********************"
                      ***********************",
     "accept": "application/json",
}

url = "https://api.themoviedb.org/3/search/movie"


class UpdateForm(FlaskForm):
    rating = FloatField(label="Your rating out of 10! eg.6.4", validators=[DataRequired()])
    review = StringField(label="Enter your Personal review!", validators=[DataRequired()])
    submit = SubmitField(label="Submit")


class Add(FlaskForm):
    add_movie = StringField(label="Enter a Movie Name", validators=[DataRequired()])
    add_button = SubmitField("Add Movie")


@app.route("/")
def home():
    # TODO : Read records
    results = database.session.execute(database.select(MovieRecord).order_by(MovieRecord.rating)).scalars().all()
    results = results[::-1]
    for i in range(len(results)):
        results[i].ranking = len(results) - i
    database.session.commit()

    return render_template("index.html", movies=results)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = UpdateForm()
    idn = request.args.get("id")
    movie = database.get_or_404(MovieRecord, idn)
    if form.validate_on_submit():
        print(f"validate on the id: {idn}")
        new_rating = float(form.rating.data)
        new_review = form.review.data
        movie.review = new_review
        movie.rating = new_rating
        database.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=form,  movie=movie)


@app.route("/delete/<int:id>")
def delete(id):
    print(id)
    current_movie = database.get_or_404(MovieRecord, id)
    database.session.delete(current_movie)
    database.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    movie_form = Add()
    if movie_form.validate_on_submit():
        movie_name = movie_form.add_movie.data.title()
        query = {"query": movie_name}
        response = requests.get(url=url, headers=headers, params=query).json()
        response = response['results']
        return render_template('select.html', search_data=response)

    return render_template("add.html", form=movie_form)


@app.route("/find")
def find():
    searched_movie_id = request.args.get("id")
    print(f'movie id you are looking for is: {searched_movie_id}')
    movie_id = searched_movie_id
    if movie_id:
        detail_api = f"https://api.themoviedb.org/3/movie/{searched_movie_id}"
        detail_response = requests.get(url=detail_api, headers=headers).json()

        new_movie = MovieRecord(
            title=detail_response['original_title'],
            year=int(detail_response['release_date'].split("-")[0]),
            description=detail_response['overview'],
            rating=0,
            ranking=0,
            review="",
            img_url=f"https://image.tmdb.org/t/p/w500/{detail_response['poster_path']}"
        )
        database.session.add(new_movie)
        database.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
