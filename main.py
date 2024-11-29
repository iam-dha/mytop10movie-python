from wsgiref.validate import header_re

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import requests
from dotenv import load_dotenv
import os
MOVIE_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
MOVIE_DETAIL_ENDPOINT = "https://api.themoviedb.org/3/movie/{movie_id}"

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
bootstrap = Bootstrap5(app)
access_token = os.environ['access_token']


# CREATE DB
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class= Base)
# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    title: Mapped[str] = mapped_column(String(250), unique= True, nullable= False)
    year: Mapped[int] = mapped_column(Integer, nullable= False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-collection.db"
db.init_app(app)

with app.app_context():
    db.create_all()
    # second_movie = Movie(
    #     title="Avatar The Way of Water",
    #     year=2022,
    #     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
    #     rating=7.3,
    #     ranking=9,
    #     review="I liked the water.",
    #     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
    # )
    # db.session.add(second_movie)
    # db.session.commit()

# CREATE EDIT FORM
class Form(FlaskForm):
    rating = StringField(label='Your rating out of 10 e.g 7.5', validators=[DataRequired()])
    review = StringField(label='Your Review', validators=[Length(max= 75)])
    submit = SubmitField(label='Done')

class AddForm(FlaskForm):
    movie = StringField(label = 'Movie Title', validators=[DataRequired()])
    submit = SubmitField(label= 'Add Movie')

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    tmp = result.scalars()
    movie_list = list(tmp)
    return render_template("index.html", movies = movie_list)

@app.route("/edit", methods = ['GET', 'POST'])
def edit():
    my_form = Form()
    movie_id = request.args.get('id')
    movie = db.get_or_404(Movie, movie_id)
    if my_form.validate_on_submit():
        movie.rating = my_form.rating.data
        form_review = my_form.review.data
        if form_review:
            movie.review = form_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html',form = my_form, movie = movie )

@app.route('/delete', methods = ['GET', 'POST'])
def delete():
    movie_id = request.args.get('id')
    movie_to_del = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_del)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods = ['GET', 'POST'])
def add():
    header = {
        'Authorization': f"Bearer {access_token}"
    }
    movie_id = request.args.get('id')
    if request.method == 'GET' and movie_id:
        endpoint = MOVIE_DETAIL_ENDPOINT.format(movie_id = movie_id)
        response = requests.get(url= endpoint, headers= header)
        movie_detail = response.json()
        new_movie = Movie(
            title=movie_detail['title'],
            year=movie_detail['release_date'].split('-')[0],
            description=movie_detail['overview'],
            img_url=f"https://image.tmdb.org/t/p/original{movie_detail['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id = new_movie.id))
    add_form = AddForm()
    if add_form.validate_on_submit():
        movie_to_add = add_form.movie.data
        params = {
            'query': f"{movie_to_add}"
        }
        response = requests.get(url=MOVIE_ENDPOINT, headers= header, params= params)
        movie_list = response.json()['results']
        return render_template('select.html', movies = movie_list)
    return render_template('add.html', form = add_form)

if __name__ == '__main__':
    app.run(debug=True, port= 8000)
