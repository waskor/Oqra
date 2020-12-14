import cv2
from PIL import Image
import generateqr as gqr

#detect and store locations for QR codes in input template using shape recognition
def find_squares(templatefile):

    global squares_sort

    template = cv2.imread(templatefile)

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

#generate a qr code and place onto an empty square on the sticker template
def place_qr_codes(templatefile):

    template_qr = Image.open(templatefile)
    gqr.initialise()
    pages = gqr.links.shape[0]//squares_sort.shape[0]
    page = 0
    sq = 0

    for i in range(gqr.links.shape[0]):

        if i % squares_sort.shape[0] == 0 and i != 0:


            fileout = "grollz/stickers/templateqr_{}.png".format(page)
            template_qr.save(fileout)
            page += 1
            sq = 0

            template_qr = Image.open(templatefile)

            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 

            sq = 1

        elif i == (gqr.links.shape[0]-1):
            
            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 
            filename = "grollz/stickers/templateqr_{}.png".format(page)
            template_qr.save(fileout)
            #gqr.links.to_csv("links2.csv")

        else:
            gqr.generate_qr(i)
            gqr.qrimg = gqr.qrimg.rotate(270)
            gqr.qrimg = gqr.qrimg.resize((squares_sort[sq,3], squares_sort[sq,2]))
            
            template_qr.paste(gqr.qrimg, (squares_sort[sq,0], squares_sort[sq,1])) 
            
            sq += 1

def main():
    templatefile = "grollz/template300.png"
    find_squares(templatefile)
    place_qr_codes(templatefile)
    

if __name__ == '__main__':

    main()

