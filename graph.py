import matplotlib.pyplot as plt
import io
import numpy


def get_graph(category_list, summ_list):
    dpi = 80
    fig = plt.figure(dpi = dpi, figsize = (512 / dpi, 384 / dpi) )
    #mpl.rcParams.update({'font.size': 10})

    plt.title('График расходов')

    index = range(len(category_list))

    plt.pie(summ_list, labels=category_list, autopct='%.1f')
    plt.axis("equal")

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    f1 = buf.read()
    return f1


