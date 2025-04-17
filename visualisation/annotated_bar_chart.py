"""Create bar chart with annotated labels on top."""
import matplotlib.pyplot as plt

def plot_annotated_bar(data, labels, title=""):
    fig, ax = plt.subplots()
    bars = ax.bar(labels, data)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{bar.get_height():.1f}', ha='center', va='bottom')
    ax.set_title(title)
    plt.show()