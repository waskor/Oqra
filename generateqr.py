import qrcode
import pandas as pd
import cProfile
import io

def initialise(linksfile):

    global links, qr

    # try:
    #     os.mkdir('qrimgs')#str(mainwindow.outputfolder) + 'qrimgs')
    # except:
    #     None

    links = pd.read_csv(linksfile)
    links['status'] = 'unused'

    qr = qrcode.QRCode(
    None,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=2,
    )


def generate_qr(i):
    
    global buf

    link = links.values[i,1]
    qr.add_data(link)
    qr.make(fit=True)
    qrimg = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    qrimg.save(buf, format='PNG')

    qr.data_list.clear()
    links.at[i,'status'] = 'used'