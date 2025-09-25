correlation_code = f'''
    numeric_df = df.select_dtypes(include=['number'])
    plt.figure(figsize=(12, 10))
    correlation_matrix = numeric_df.corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title('Matriz de Correlação - Dataset Completo')
    plt.tight_layout()
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
'''