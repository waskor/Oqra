import qrcode
import pandas as pd

def initialise():

    global links, qr

    filename = "grollz/links.csv"
    links = pd.read_csv(filename)

    qr = qrcode.QRCode(
    None,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=2,
    )


def generate_qr(i):
    
    global qrimg

    link = links.values[i,1]
    qr.add_data(link)
    qr.make(fit=True)
    qrimg = qr.make_image(fill_color="black", back_color="white")

    qr.data_list.clear()

