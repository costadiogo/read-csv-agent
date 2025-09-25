variability_code = f'''
    numeric_cols = df.select_dtypes(include=['number']).columns
    print("=== MEDIDAS DE VARIABILIDADE ===")

    for col in numeric_cols:
        std_val = df[col].std()
        var_val = df[col].var()
        range_val = df[col].max() - df[col].min()
        
        print(f"**{{col}}**:")
        print(f"  - Desvio Padrão: {{std_val:.4f}}")
        print(f"  - Variância: {{var_val:.4f}}")
        print(f"  - Amplitude: {{range_val:.4f}}")
        print()

    # Gráfico de desvios padrão
    plt.figure(figsize=(12, 6))
    stds = [df[col].std() for col in numeric_cols]
    plt.bar(numeric_cols, stds)
    plt.title('Desvio Padrão de Cada Variável')
    plt.xlabel('Variáveis')
    plt.ylabel('Desvio Padrão')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()

    print('{{"answer": "Medidas de variabilidade calculadas para todas as variáveis numéricas baseado nos registros do dataset."}}')
'''