--- INICIANDO DETECTOR DE MUTACIONES ---


[FASE]: MUTADOR_LOGICO
 Para cumplir con tus instrucciones, primero necesitamos clonar el repositorio y luego buscar una función lógica para modificarla. A continuación, se muestra cómo hacerlo utilizando Python:

```python
import os
import git
import encoding

def clone_and_scan_for_testing(repo_url):
    repo = git.Repo.clone_from(repo_url)
    for file in repo.iterdir():
        if file.is_file and (".py" in str(file)):
            with open(str(file), encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    if "def" in line and ":" in line:
                        function_name, _ = line.split(":")
                        function_name = function_name.strip()
                        function_content = ""
                        for line in lines[lines.index(function_name)+1:]:
                            if not "def" in line and not ":" in line:
                                function_content += line
                        # Buscar una función lógica y modificar el operador (==, !=, <, >)
                        if "def is_valid(self, number):" in function_content:
                            lines[lines.index("    return self.number == 5")] = f"    return self.number > 5"
                        # Guardar el archivo modificado
                        with open(str(file), "w", encoding="utf-8") as f:
                            for line in lines:
                                f.write(line)

# Ejecuta la función con el repositorio que deseas analizar
clone_and_scan_for_testing("https://github.com/usuario/repo")
```

Este código clona el repositorio y busca una función lógica llamada `is_valid`. Luego, modifica el operador de comparación (==) a (>) para intentar engañar al test.
------------------------------------------------------------

[FASE]: EJECUTOR_DE_TESTS
 Para ejecutar el código proporcionado, primero necesitamos instalar la biblioteca gitpython utilizando pip:

```bash
pip install gitpython
```

Después, copie y pegue el código en un archivo `mutation_tester.py`. A continuación, ejecute el siguiente comando para clonar el repositorio especificado y modificar la función lógica:

```bash
python mutation_tester.py "https://github.com/usuario/repo"
```

Después de ejecutar el código, se modifica el archivo del repositorio y se guarda en la misma ubicación donde fue clonado. A continuación, se puede verificar si el test pasaría a pesar del error mediante el siguiente comando:

```bash
python -m unittest disco.test
```

En este caso, el código modifica la función `is_valid` para que devuelva true cuando el número es mayor que 5 en lugar de igual a 5. Si el test pasa, significa que el cambio no fue detectado y el mutante sobrevivió.

Para verificar si el mutante sobrevive o no, necesitamos tener un archivo `test_disco.py` en el repositorio con los tests correspondientes a la función `is_valid`. Si el test pasa, significa que el mutante sobrevivió y el resultado sería:

```bash
MUTATION SURVIVED
```

Si el test falla, significa que el mutante fue detectado y el resultado sería:

```bash
MUTATION KILLED
```
------------------------------------------------------------

[FASE]: AUDITOR_DE_ROBUSTEZ
 Para evaluar la robustez de la suite de pruebas en este caso, debemos verificar si el mutante sobrevive o no. Si el mutante sobrevive, significa que la suite de pruebas no está cubriendo correctamente los valores límite (edge cases) y necesita ser mejorada.

Para evaluar la robustez de la suite de pruebas, primero debemos asegurarnos de tener un archivo `test_disco.py` en el repositorio con los tests correspondientes a la función `is_valid`. Luego, ejecutamos el código proporcionado para modificar la función lógica y verificar si el mutante sobrevive o no:

```bash
python mutation_tester.py "https://github.com/usuario/repo"
python -m unittest disco.test
```

Si el test pasa, significa que el mutante sobrevivió y la suite de pruebas no está cubriendo correctamente los valores límite (edge cases). En este caso, se necesitan tests adicionales para cubrir los valores límite en la función `is_valid`.

Para cubrir los valores límite, podemos agregar los siguientes tests a `test_disco.py`:

```python
def test_is_valid_less_than_5(self):
    self.assertFalse(disco.Disco(4).is_valid())

def test_is_valid_equal_to_5(self):
    self.assertTrue(disco.Disco(5).is_valid())

def test_is_valid_greater_than_5(self):
    self.assertTrue(disco.Disco(6).is_valid())
```

Estos tests cubren los valores límite (edge cases) para la función `is_valid`. Si se agrega este código a `test_disco.py`, el mutante será detectado y el resultado sería:

```bash
MUTATION KILLED
```

Esto significa que la suite de pruebas está cubriendo correctamente los valores límite (edge cases) en la función `is_valid`.
------------------------------------------------------------