from django.shortcuts import render, redirect
from django.http import JsonResponse
import socket
import json

def index(request):
    return render(request, 'index.html')

def process_request(request):
    if request.method == 'POST':
        palabra = request.POST.get('palabra')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        if palabra and fecha_inicio and fecha_fin:
            # Redirigir a la vista de resultados
            return redirect('results', palabra=palabra, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        else:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

    return JsonResponse({'error': 'This endpoint only accepts POST requests.'}, status=405)

def send_and_receive_data(flag, palabra=None, fecha_inicio=None, fecha_fin=None):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # client_socket.connect(("172.26.253.21", 9999))
    client_socket.connect(("127.0.0.1", 9999))
    result = []

    try:
        client_socket.sendall(f"{flag}\n".encode())

        if flag == 0:  # Procesar archivos con palabra y fechas
            client_socket.sendall(f"{palabra}\n".encode())
            client_socket.sendall(f"{fecha_inicio}\n".encode())
            client_socket.sendall(f"{fecha_fin}\n".encode())
        elif flag == 1:  # Contar las 100 palabras más frecuentes
            pass  # No se envían datos adicionales para este caso

        buffer = ''
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            buffer += data.decode()
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                result.append(line.strip())
    finally:
        client_socket.close()

    return result

def show_results(request, palabra, fecha_inicio, fecha_fin):
    data = send_and_receive_data(0, palabra=palabra, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    print("Datos recibidos del servidor socket:")
    for line in data:
        print(line)
    labels = []
    values = []

    for line in data:
        if line.strip():
            parts = line.strip().split(', ')
            if len(parts) == 2:
                fecha = parts[0]
                valor = float(parts[1])
                labels.append(fecha)
                values.append(valor)

    labels_sorted = sorted(labels)
    chart_title = f"Análisis de sentimiento de la palabra '{palabra}' entre las fechas {fecha_inicio} y {fecha_fin}"

    context = {
        'chart_title': chart_title,
        'labels': json.dumps(labels_sorted),
        'values': json.dumps(values),
        'palabra': palabra,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'results.html', context)
    
def show_word_cloud_results(request):
    try:
        print("Iniciando función show_word_cloud_results")
        
        # Llamar a la función para enviar y recibir datos del servidor
        data = send_and_receive_data(1)

        # Datos recibidos del servidor socket
        print("Datos recibidos del servidor socket:")
        for line in data:
            print(line)

        # Procesar los datos recibidos para la visualización del cloud map
        values = []
        for item in data:
            word, count = item.split(', ')
            values.append({'text': word, 'size': int(count)})
            
        context = {

            'data': json.dumps(values)
        }
        print(context)


        return render(request, 'word_cloud.html', context)

    except Exception as e:
        # En caso de error, retornar una respuesta JSON con el error
        print(f"Error en la función show_word_cloud_results: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

