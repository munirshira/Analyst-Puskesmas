from flask import Flask,render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os
import datetime
import pandas as pd
import io
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn import metrics
import json
import plotly
import plotly.express as px

now = datetime.datetime.now()
ts = datetime.datetime.timestamp(now)

app = Flask(__name__)
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'klaster'
app.config['UPLOAD_FOLDER'] = 'files'
basedir = os.path.abspath(os.path.dirname(__file__))

mysql = MySQL(app)
@app.route('/')
def form():
    return render_template('form.html')
 

@app.route('/uploader', methods = ['POST', 'GET'])
def uploader():
    if request.method == 'POST':
        jumlah = request.form['jumlah']
        excel = request.files['excel']
        extension = os.path.splitext(secure_filename(excel.filename))[1]
        file = str(ts) + extension
        excel.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], file))
        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO file (nama_file,jumlah,tgl_file) VALUES(%s,%s,%s)''',(file,jumlah,now.strftime('%Y-%m-%d %H:%M:%S')))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('visualisasi'))

@app.route('/visualisasi')
def visualisasi():
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT nama_file, jumlah FROM file ORDER BY id_file DESC LIMIT 1''')
        table = cursor.fetchall()
        cursor.close()
        table = str(table)
        table = table[3:-3]
        n=int(table[-1])
        table = table[:-4]
        cwd = os.getcwd()
        data = pd.read_excel(f'{cwd}\\venv\\files\\'+table)
        data = data[(data.Jumlah_Dokter_Umum > 0) & (data.Jumlah_Perawat > 0) & (data.Jumlah_Bidan > 0)]
        x = data.iloc[:,1:]
        scaler = MinMaxScaler()
        scale = scaler.fit_transform(x[['Jumlah_Tempat_Tidur','Jumlah_Ambulance','Jumlah_Puskesmas_Keliling_Roda_Empat','Jumlah_Puskesmas_Pembantu','Jumlah_Dokter_Umum','Jumlah_Dokter_Gigi','Jumlah_Perawat','Jumlah_Bidan','Jumlah_Farmasi','Jumlah_Kesehatan_Masyarakat','Jumlah_Kesehatan_Lingkungan','Jumlah_Tenaga_Gizi','Jumlah_Tenaga_Ahli_Teknologi_Laboratorium_Medik','Jumlah_Tenaga_Non_Medis']])
        df_scale = pd.DataFrame(scale, columns = ['Jumlah_Tempat_Tidur','Jumlah_Ambulance','Jumlah_Puskesmas_Keliling_Roda_Empat','Jumlah_Puskesmas_Pembantu','Jumlah_Dokter_Umum','Jumlah_Dokter_Gigi','Jumlah_Perawat','Jumlah_Bidan','Jumlah_Farmasi','Jumlah_Kesehatan_Masyarakat','Jumlah_Kesehatan_Lingkungan','Jumlah_Tenaga_Gizi','Jumlah_Tenaga_Ahli_Teknologi_Laboratorium_Medik','Jumlah_Tenaga_Non_Medis'])
        pca = PCA(3)
        pca_data = pca.fit_transform(df_scale)
        model = KMeans(n_clusters = n, init = "k-means++", n_init=10)
        label = model.fit_predict(pca_data)
        sil = metrics.silhouette_score(pca_data, model.labels_, metric='euclidean')
        wcss = []
        wcss.append(model.inertia_)
        pca_data = pd.DataFrame(data=pca_data, columns=['PC1','PC2','PC3'])
        vis = pca_data
        vis['hasil'] = label
        hasil=data
        hasil['Klaster']=label
        fig = px.scatter_3d(vis, x='PC1', y='PC2', z='PC3',color='hasil')
        trid = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        pca_data = pca_data.iloc[: , :-1]
        data = data.iloc[: , :-1]
        return render_template('visualisasi.html', df_scale=df_scale.to_html(classes=["table", "table-bordered", "table-striped", "table-hover"]), data=data.to_html(classes=["table", "table-bordered", "table-striped", "table-hover"]), pca_data=pca_data.to_html(classes=["table", "table-bordered", "table-striped", "table-hover"]), hasil=hasil.to_html(classes=["table", "table-bordered", "table-striped", "table-hover"]), sil=sil, wcss=wcss, trid=trid)


if __name__== '__main__':
    app.run()