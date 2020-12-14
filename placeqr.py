import cv2
import numpy as np
from PIL import Image
import glob
import generateqr as gqr
import time 
import cProfile

start_time = time.time()

def find_squares():

    global squares_sort

    template = cv2.imread("grollz/template300.png")

    squares_list = []

    templategray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    ret, thresh = cv2.threshold(templategray,127,255,cv2.THRESH_BINARY_INV)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:    

        x,y,w,h = cv2.boundingRect(c)

        if w>80:
            
            accuracy = 0.01*cv2.arcLength(c,True)
            approx = cv2.approxPolyDP(c,accuracy,True)
            x,y,w,h = cv2.boundingRect(approx)
            cv2.rectangle(template,(x,y),(x+w,y+h),255,1)
            square = [x-2,y-2,w+4,h+4]
            squares_list.append(square)

    squares = np.array(squares_list)
    ind = np.lexsort((squares[:,1],squares[:,0])) 
    squares_sort = squares[ind]
    cv2.imwrite('squares.jpg', template)
    

#template = cv2.resize(template, (0,0), fx=0.15, fy=0.15) 


def place_qr_codes():

    template_qr = Image.open("grollz/template300.png")
    template_qr_clear = Image.open("grollz/template300.png")
    gqr.initialise()
    pages = gqr.links.shape[0]//squares_sort.shape[0]
    page = 0
    sq = 0

    for i in range(gqr.links.shape[0]):

        if i % squares_sort.shape[0] == 0 and i != 0:


            filename = "grollz/stickers/templateqr_{}.png".format(page)
            template_qr.save(filename)
            page += 1
            sq = 0

            template_qr = Image.open("grollz/template300.png")

            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 

            sq = 1

        elif page == pages and i != (gqr.links.shape[0]-1):
            
            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 

            sq += 1

        elif i == (gqr.links.shape[0]-1):
            
            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 
            filename = "grollz/stickers/templateqr_{}.png".format(page)
            template_qr.save(filename)

        else:
            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 
            
            sq += 1

def main():
    
    find_squares()
    place_qr_codes()

 


if __name__ == '__main__':
    #cProfile.run('main()')
    main()

print("--- %s seconds ---" % (time.time() - start_time))

# def place_qr_codes(template):

    # template_qr = Image.open("grollz/template_hq.png")
    # i = 0

    # #for f in glob.iglob("C:/Users/Was/Documents/Python/grollz/qrcodes/*.png"):
    # for i in range(8)

    #     qr = Image.open(f)
    #     #qr = qr.rotate(270)
    #     qr = qr.resize((squares_sort[i,3], squares_sort[i,2]))
        
    #     template_qr.paste(qr, (squares_sort[i,0], squares_sort[i,1])) 
    #     i += 1

    # template_qr.save('grollz/templateqr.png')
