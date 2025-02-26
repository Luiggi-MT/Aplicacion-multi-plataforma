from flask import Blueprint, jsonify, request
from db_controller import DatabaseController

# Crear el Blueprint
userBP = Blueprint('views', __name__)

# Instanciar el controlador de la base de datos
db_controller = DatabaseController()

# Función para obtener la foto de perfil desde la tabla MULTIMEDIA
def obtener_foto_perfil(nombre_usuario):
    try:
        query = "SELECT id FROM MULTIMEDIA WHERE username = %s AND tipo = 'FOTO' LIMIT 1"
        result = db_controller.fetch_query(query, (nombre_usuario,))
        if result and result[0]:
            return f"http://{request.host}/visualiza/{result[0][0]}"
        else:
            return "https://st3.depositphotos.com/3538469/15750/i/450/depositphotos_157501024-stock-photo-business-man-icon.jpg"
    except Exception as e:
        print(f"Error al obtener la foto de perfil: {str(e)}", e)
        return "https://st3.depositphotos.com/3538469/15750/i/450/depositphotos_157501024-stock-photo-business-man-icon.jpg"


def obtener_usuarios_por_rol(rol):
    """Función común para obtener usuarios por rol"""
    query = "SELECT * FROM USUARIO WHERE rol = %s"
    results = db_controller.fetch_query(query, (rol,))
    
    usuarios = []  # Inicializamos una lista vacía para los usuarios

    if results:
        for result in results:
            nombre_usuario = result['nombre_usuario'] if result['nombre_usuario'] else "No disponible"
            foto_perfil = obtener_foto_perfil(nombre_usuario)
            usuario = {
                'id': result['id'],
                'nombre': result['nombre'] if result['nombre'] else "No disponible",
                'apellido': result['apellidos'] if result['apellidos'] else "No disponible",
                'nombre_usuario': nombre_usuario,
                'contraseña': result['contraseña'] if result['contraseña'] else "No disponible",
                'color_tema': result['color_fondo'] if result['color_fondo'] else "#FFFFFF",
                'tamaño_letra': result['tamaño_letra'] if result['tamaño_letra'] else "14px",
                'foto_perfil': foto_perfil,
                'pref_contenido': result['pref_contenido']
            }
            usuarios.append(usuario)
    return usuarios


@userBP.route('/estudiantes', methods=['GET'])
def estudiantes():
    """Obtener lista de estudiantes"""
    estudiantes = obtener_usuarios_por_rol('ESTUDIANTE')
    return jsonify(estudiantes)  # Siempre retornamos la lista (vacía si no hay usuarios)


@userBP.route('/profesores', methods=['GET'])
def profesores():
    """Obtener lista de profesores"""
    profesores = obtener_usuarios_por_rol('PROFESOR')
    return jsonify(profesores)  # Siempre retornamos la lista (vacía si no hay profesores)
@userBP.route('/profesores', methods=['POST'])
def create_profesor():
    """Crear un nuevo profesor"""
    data = request.get_json()
    
    # Verifica que todos los campos necesarios estén presentes
    required_fields = ['nombre', 'apellido', 'nombre_usuario', 'contraseña', 'tipo_usuario']
    if not all(field in data for field in required_fields):
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({"error": f"Faltan los siguientes campos: {', '.join(missing_fields)}"}), 400
    
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    nombre_usuario = data.get('nombre_usuario')
    contraseña = data.get('contraseña')
    tipo_usuario = data.get('tipo_usuario')
    color_tema = data.get('color_tema', '#FFFFFF')
    tamaño_letra = data.get('tamaño_letra', '14px')
    
    # Consultar si ya existe un usuario con el mismo nombre de usuario
    query_check = "SELECT COUNT(*) FROM USUARIO WHERE nombre_usuario = %s"
    result = db_controller.fetch_query(query_check, (nombre_usuario,))
    if result and result[0][0] > 0:
        return jsonify({"error": "El nombre de usuario ya está registrado"}), 400
    
    # Insertar los datos del profesor en la base de datos
    query_insert = """
        INSERT INTO USUARIO (nombre, apellidos, nombre_usuario, contraseña, rol, color_fondo, tamaño_letra)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        db_controller.execute_query(query_insert, (nombre, apellido, nombre_usuario, contraseña, tipo_usuario, color_tema, tamaño_letra))
        # Después de insertar, obtener la lista completa de profesores
        profesores = obtener_usuarios_por_rol("PROFESOR")
        return jsonify(profesores), 201  # Devolver la lista de profesores
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Construir la consulta para insertar los datos del nuevo profesor
@userBP.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    """Actualizar la contraseña de un profesor"""
    data = request.get_json()
    # Verifica que el campo contraseña esté presente
    if 'contraseña' not in data:
        return jsonify({"error": "No hay datos válidos para actualizar"}), 400
    
    # Construir la consulta para actualizar la contraseña
    update_query = "UPDATE USUARIO SET contraseña = %s WHERE id = %s"
    values = (data['contraseña'], id)
    
    try:
        db_controller.execute_query(update_query, values)
        return jsonify({"success": "Contraseña actualizada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@userBP.route('/admins', methods=['GET'])
def admins():
    """Obtener lista de administradores"""
    admins = obtener_usuarios_por_rol('ADMINISTRADOR')
    return jsonify(admins)  # Siempre retornamos la lista (vacía si no hay administradores)


@userBP.route("/estudiantes/<int:id>", methods=["DELETE"])
def delete_estudiante(id):
    """Eliminar un estudiante"""
    query = "DELETE FROM USUARIO WHERE id = %s"
    try:
        db_controller.execute_query(query, (id,))
        return jsonify({"success": "Estudiante eliminado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@userBP.route("/estudiantes/<int:id>", methods=["PUT"])
def put_estudiante(id):
    """Actualizar los datos de un estudiante"""
    data = request.get_json()

    # Verifica que al menos uno de los campos sea válido para actualizar
    if not any([data.get(key) for key in ['apellidos', 'color_fondo', 'contraseña', 'foto_perfil', 'id', 'nombre', 'nombre_usuario', 'supervisado_por', 'tamaño_letra', 'tipo_usuario', 'pref_contenido']]):
        return jsonify({"error": "No hay datos válidos para actualizar"}), 400
    
    # Construir la consulta dinámica para actualizar solo los campos necesarios
    campos_a_actualizar = []
    valores = []
    if data.get('apellidos'): 
        campos_a_actualizar.append("apellidos = %s")
        valores.append(data['apellidos'])
    if data.get('color_fondo'):
        campos_a_actualizar.append("color_fondo = %s")
        valores.append(data['color_fondo'])
    if data.get('contraseña'):
        campos_a_actualizar.append("contraseña = %s")
        valores.append(data['contraseña'])
    if data.get('nombre'):
        campos_a_actualizar.append("nombre = %s")
        valores.append(data['nombre'])
    if data.get('tamaño_letra'):
        campos_a_actualizar.append("tamaño_letra = %s")
        valores.append(data['tamaño_letra'])
    if data.get('nombre_usuario'): 
        campos_a_actualizar.append("nombre_usuario = %s")
        valores.append(data['nombre_usuario'])
    if data.get('rol'): 
        campos_a_actualizar.append("rol = %s")
        valores.append(data['rol'])
    if data.get('rol'): 
        campos_a_actualizar.append("pref_contenido = %s")
        valores.append(data['pref_contenido'])
    
    # Siempre actualizamos la última actualización
    #ultima_actualizacion = "NOW()"
    #valores.append(ultima_actualizacion)
    #campos_a_actualizar.append("ultima_actualizacion = %s")
    
    # Agregar el id al final 
    valores.append(id)

    # Crear la consulta 
    query = f"""
        UPDATE USUARIO
        SET {', '.join(campos_a_actualizar)}
        WHERE id = %s
    """

    try:
        db_controller.execute_query(query, valores)
        return jsonify({"success": "Estudiante actualizado exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@userBP.route("/estudiantes", methods=["POST"])
def post_estudiante():
    """Crear un nuevo estudiante y devolver la lista completa de estudiantes"""
    data = request.get_json()

    # Verifica que los campos esenciales estén presentes
    required_fields = ['nombre', 'apellido', 'nombre_usuario', 'contraseña', 'rol']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos necesarios"}), 400

    # Asignar valores de los campos recibidos
    nombre = data.get('nombre')
    apellidos = data.get('apellido')
    nombre_usuario = data.get('nombre_usuario')
    contraseña = data.get('contraseña')
    rol = data.get('rol', 'ESTUDIANTE')  # Rol predeterminado es ESTUDIANTE
    color_fondo = data.get('color_fondo', '#F8F8F8')  # Valor predeterminado para color_fondo
    tamaño_letra = data.get('tamaño_letra', '14px')  # Valor predeterminado para tamaño_letra


    # Consultar si ya existe un usuario con el mismo nombre de usuario
    query_check = "SELECT COUNT(*) FROM USUARIO WHERE nombre_usuario = %s"
    result = db_controller.fetch_query(query_check, (nombre_usuario,))
    if result and result[0][0] > 0:
        return jsonify({"error": "El nombre de usuario ya está registrado"}), 400

    # Insertar los datos del estudiante en la base de datos
    query_insert = """
        INSERT INTO USUARIO (nombre, apellidos, nombre_usuario, contraseña, rol, color_fondo, tamaño_letra)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:
        db_controller.execute_query(query_insert, (nombre, apellidos, nombre_usuario, contraseña, rol, color_fondo, tamaño_letra))
        
        # Después de insertar, obtener la lista completa de estudiantes
        estudiantes = obtener_usuarios_por_rol("ESTUDIANTE")
        
        return jsonify(estudiantes), 201  # Devolver la lista de estudiantes
    except Exception as e:
        return jsonify({"error": str(e)}), 500
