average_code = f'''
    numeric_cols = df.select_dtypes(include=['number']).columns
    print("=== MEDIDAS DE TENDÊNCIA CENTRAL ===")

    for col in numeric_cols:
        mean_val = df[col].mean()
        median_val = df[col].median()
        try:
            mode_val = df[col].mode().iloc[0] if len(df[col].mode()) > 0 else "N/A"
        except:
            mode_val = "N/A"
        
        print(f"**{{col}}**:")
        print(f"  - Média: {{mean_val:.4f}}")
        print(f"  - Mediana: {{median_val:.4f}}")
        print(f"  - Moda: {{mode_val}}")
        print()

    # Gráfico comparativo
    plt.figure(figsize=(14, 8))
    means = [df[col].mean() for col in numeric_cols]
    medians = [df[col].median() for col in numeric_cols]

    x = range(len(numeric_cols))
    width = 0.35

    plt.bar([i - width/2 for i in x], means, width, label='Média', alpha=0.7)
    plt.bar([i + width/2 for i in x], medians, width, label='Mediana', alpha=0.7)

    plt.title('Comparação: Média vs Mediana')
    plt.xlabel('Variáveis')
    plt.ylabel('Valores')
    plt.xticks(x, numeric_cols, rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()

    print('{{"answer": "Medidas de tendência central calculadas para todas as variáveis numéricas baseado nos registros do dataset."}}')
'''