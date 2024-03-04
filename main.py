from website import create_app

app = create_app()

PORT = 3000

if __name__ == '__main__':
    app.run(debug = True,host = "0.0.0.0",port = PORT)