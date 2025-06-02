import trimesh
import numpy as np

# Carga la malla STL (ajusta el nombre y ruta)
mesh = trimesh.load_mesh("Brazo1C.STL")

# Escalar la malla si aplicaste 'scale' en MuJoCo
# Por ejemplo: scale="0.005 0.005 0.005"
scale = [0.005, 0.005, 0.005]
mesh.apply_scale(scale)

# Define la densidad del material (ejemplo: aluminio ≈ 2700 kg/m³)
density = 2700  # puedes ajustar esto según el material

# Calcula la masa total, COM, y el tensor de inercia
mass_props = mesh.mass_properties(density=density)

print("\n--- PROPIEDADES FÍSICAS ---")
print(f"Masa total: {mass_props['mass']:.4f} kg")
print(f"Centro de masa: {mass_props['center_mass']} (en metros)")
print(f"Inercia (tensor 3x3):\n{mass_props['inertia']}")

# Si MuJoCo solo usa diagonal de inercia:
inertia_diagonal = np.diag(mass_props['inertia'])
print(f"Momento de inercia diagonal: {inertia_diagonal}")