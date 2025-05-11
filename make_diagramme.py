import matplotlib.pyplot as plt


def stat_img(data):
    plt.style.use('_mpl-gallery-nogrid')
    labels, vals = zip(*data.items())
    fig, ax = plt.subplots(figsize=(5, 5))  # Размер в дюймах
    ax.pie(vals, labels=labels, autopct='%1.1f%%', shadow=True,
           wedgeprops={'lw': 1, 'edgecolor': "k"})
    ax.axis("equal")

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
    plt.savefig('static/img/stat.png', dpi=300)


stat_img({'q': 1, 'w': 2})
