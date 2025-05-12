import matplotlib.pyplot as plt


def stat_img(data):
    plt.style.use('_mpl-gallery-nogrid')
    labels = []
    vals = []
    for i in data:
        labels.append(i[0])
        vals.append(i[1])
    print(labels, vals)
    fig, ax = plt.subplots(figsize=(5, 5))  # Размер в дюймах
    ax.pie(vals, labels=labels, autopct='%1.1f%%', shadow=True,
           wedgeprops={'lw': 1, 'edgecolor': "k"})
    ax.axis("equal")
    fig.tight_layout()
    plt.savefig('static/img/stat.png', dpi=300)

