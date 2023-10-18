import numpy as np
from PIL import Image
import pandas as pd
from flask import Flask, render_template, request, session, abort
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from flask_bootstrap import Bootstrap
import os
from werkzeug.utils import secure_filename

# Defining upload folder path
UPLOAD_FOLDER = os.path.join("static")
# Define allowed files
ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif']

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)
Bootstrap(app)

# Configure upload folder for Flask application
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["UPLOAD_EXTENSIONS"] = ALLOWED_EXTENSIONS


# Create form to upload file
class UploadForm(FlaskForm):
    file = FileField("Select an image file:")
    submit = SubmitField("Get Colour Pallette")


def get_palette(img):
    """Gets RGB values of ten most common colours from an image. Returns pandas dataframe."""
    # Open image and make array of RBG values
    img = Image.open(img).convert("RGB")
    img_array = np.array(img)

    # Convert 3D array to 2D array
    shape = img_array.shape
    flat_array = np.reshape(img_array, ((shape[0] * shape[1]), shape[2]))

    # Convert array to dataframe and get unique rows
    df = pd.DataFrame(flat_array, columns=["R", "G", "B"])
    unique_values = df.value_counts()

    # Get top ten and convert back to dataframe
    top_ten_series = unique_values[:10]
    top_ten_df = top_ten_series.reset_index().drop("count", axis=1)

    # Get hex codes for colours
    df_with_hex = add_hex(top_ten_df)

    return df_with_hex


def add_hex(df):
    """Converts RGB values to hex and adds a column to the dataframe"""
    hex_column = []

    # Cycle through df columns and convert values to hex
    for x in range(0, len(df)):
        rgb_list = [df.iloc[x]['R'], df.iloc[x]['G'], df.iloc[x]['B']]
        hex_list = [f'{i:02x}' for i in rgb_list]
        hex_string = "".join(hex_list)
        hex_code = f"#{hex_string}"
        hex_column.append(hex_code)

    # Add hex values to df as a new column
    df["Hex"] = hex_column

    return df


@app.route("/", methods=["GET", "POST"])
def home():
    form = UploadForm()
    img_file_path = ""
    colour_df = pd.DataFrame([0, 0, 0])
    break_point = 0

    if request.method == "POST":
        if form.validate_on_submit:
            image = form.file.data
            filename = secure_filename(image.filename)
            if filename != "":
                # If invalid filetype, give 400 error
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    abort(400)

                # Save image in session
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                session['img_filepath'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img_file_path = session.get('img_filepath', None)

                # Get dataframe of 10 most common colours by RGB and hex code
                colour_df = get_palette(img_file_path)

                # Calculate breakpoint for display formatting
                if len(colour_df) > 5:
                    break_point = int(round(len(colour_df)/2))
                else:
                    break_point = len(colour_df)

    return render_template("index.html", form=form, image=img_file_path, df=colour_df, new_row=break_point)


if __name__ == "__main__":
    app.run(debug=True)
