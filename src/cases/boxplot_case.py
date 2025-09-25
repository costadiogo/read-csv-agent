boxplot_code = f'''
    numeric_cols = df.select_dtypes(include=['number']).columns
    n_cols = len(numeric_cols)
    n_rows = (n_cols + 3) // 4
    plt.figure(figsize=(16, 4*n_rows))

    for i, col in enumerate(numeric_cols):
        plt.subplot(n_rows, 4, i+1)
        sns.boxplot(x=df[col])
        plt.title(f'{{col}}', fontsize=10)
        plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
'''