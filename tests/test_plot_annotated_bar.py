from visualisation.annotated_bar_chart import plot_annotated_bar

def test_plot_function_runs():
    # Just check that the function executes
    plot_annotated_bar([1, 2, 3], ["A", "B", "C"], title="Test")