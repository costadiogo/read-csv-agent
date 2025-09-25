interval_code = f'''
    numeric_cols = df.select_dtypes(include=['number']).columns
    print("=== INTERVALOS DAS VARIÁVEIS ===")

    for col in numeric_cols:
        min_val = df[col].min()
        max_val = df[col].max()
        print(f"**{{col}}**: [{{min_val:.2f}}, {{max_val:.2f}}] (amplitude: {{max_val-min_val:.2f}})")

    plt.figure(figsize=(12, 6))
    ranges = [(df[col].max() - df[col].min()) for col in numeric_cols]
    plt.bar(numeric_cols, ranges)
    plt.title('Amplitude (Intervalo) de Cada Variável')
    plt.xticks(rotation=45)
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()

    print('{{"answer": "Intervalos calculados para todas as variáveis numéricas baseado nos registros do dataset."}}')
'''