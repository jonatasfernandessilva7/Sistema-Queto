import matplotlib.pyplot as plt

# --- Dados fornecidos ---
# Evento de texto (valores identificados)
eventos_texto = [0, 95, 87, 80, 95, 90, 90, 85]
indices_texto = list(range(1, len(eventos_texto) + 1))

# Evento de voz (None representa "não identificado")
eventos_voz = [90, None, 90, None, 90, 90, None, 90]
indices_voz = list(range(1, len(eventos_voz) + 1))
valores_voz_plot = [v if v is not None else 0 for v in eventos_voz]
cores_voz = ['seagreen' if v is not None else 'lightgray' for v in eventos_voz]

# --- Gráfico 1: Evento de Texto ---
plt.figure(figsize=(10, 5))
plt.bar(indices_texto, eventos_texto, color='steelblue')
plt.title("Evolução do Nível de Confiança - Evento de Texto")
plt.xlabel("Relatório")
plt.ylabel("Nível de Confiança (%)")
plt.ylim(0, 100)
plt.xticks(indices_texto)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# --- Gráfico 2: Evento de Voz ---
plt.figure(figsize=(10, 5))
bars = plt.bar(indices_voz, valores_voz_plot, color=cores_voz)
plt.title("Evolução do Nível de Confiança - Evento de Voz")
plt.xlabel("Relatório")
plt.ylabel("Nível de Confiança (%)")
plt.ylim(0, 100)
plt.xticks(indices_voz)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Marcar "N/D" nas barras cinzas
for i, v in enumerate(eventos_voz):
    if v is None:
        plt.text(indices_voz[i], 5, "N/D", ha='center', va='bottom', color='black')

plt.tight_layout()
plt.show()
