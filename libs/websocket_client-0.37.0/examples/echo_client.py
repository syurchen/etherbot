from __future__ import print_function
import websocket

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.create_connection("wss://ztest.iptelefon.su:8081")
    ws.send("sid=EXTERNAL-CONNECTION-AMOCRM&uid=555400006&service=monitor&command=update&params=0001566")
    print("Sent")
    print("Receiving...")
    result = ws.recv()
    print("Received '%s'" % result)
    ws.close()
