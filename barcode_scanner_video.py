from pyzbar import pyzbar
from imutils.video import VideoStream
from bs4 import BeautifulSoup
from firebase_admin import credentials
from firebase_admin import db
import firebase_admin
import cv2
import urllib2
import datetime
import imutils
import requests
import time

#Firebase access information and firebase database URL
cred = credentials.Certificate('/home/pi/book-scann-firebase-adminsdk-ym2b5-f96f666660.json')
firebase_admin.initialize_app(cred, {'databaseURL':'https://book-scann.firebaseio.com/'})

#Barcode lookup api key
api_key = "jn2v5zbztj1o374nrafdqqz6gg4qfe" 


print("[INFO] starting video stream...")

vs = VideoStream(src=0).start()
#vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

found = set()

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=400)
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        if barcodeData not in found:
            if barcodeType == "EAN13":
                #print out scanned barcode data and type
                print "Barcode:",barcodeData," Barcode Type:",barcodeType
                
                
                #URL
                Api_url = ("https://api.barcodelookup.com/v2/products?barcode="+barcodeData+"&formatted=y&key="+api_key)
                
                #Barcode Lookup Api and response code
                response = requests.get(Api_url)
                response_status = response.status_code
                
                #404 error handling
                if response_status == 404:
                    print("404 error, cannot find URL")
                else:
                    book_data = response.json()
                    book_title = book_data['products'][0]['title']
                    book_author = book_data['products'][0]['author']
                    print "Book ",book_title
                    print "Author ",book_author
                    
                    #Firebase database reference for books
                    ref = db.reference('/books',None)
                    
                    #Get Firebase Array
                    firebase_array = ref.get()
                   
                    #Scanner Array
                    book_array = [book_title]
                    
                    #Check if firebase array is empty
                    if firebase_array is None:
                        ref.set(book_array)
                            
                    else:
                        #Check if scanned book is already in the firebase array
                        if book_title in firebase_array:
                            print "That Book is already in the database"
                    
                        else:
                            #Firebase Array combind with the scanner array
                            combined_array = firebase_array + book_array
                            
                            #Push combined array to firebase database
                            ref.set(combined_array)
                            print("Firebase database has been updated")
                    
                    #Barcode image view
                    found.add(barcodeData)
                    cv2.imshow("Barcode Scanner", frame)
                    cv2.imwrite("saved.jpg", frame)
                    key = cv2.waitKey(1) & 0xFF
                        
                    if key == ord("q"):
                        break
                
            else:
                print("Wrong Barcode Type")
            
print("[INFO] cleaning up...")
cv2.destroyAllWindows()
vs.stop()