from weave import server

s = server.HttpServer()
print(s.url)
s.run()
