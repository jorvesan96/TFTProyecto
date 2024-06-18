import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import socket

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def process_request(request):
    if request.method == 'POST':
        palabra = request.POST.get('palabra')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        if palabra and fecha_inicio and fecha_fin:

            return redirect('results', palabra=palabra, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        else:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

    return HttpResponse("This endpoint only accepts POST requests.", status=405)

def send_and_receive_data(palabra, fecha_inicio, fecha_fin):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", 9999))
    result = []

    try:
        client_socket.sendall(f"{palabra}\n".encode())
        client_socket.sendall(f"{fecha_inicio}\n".encode())
        client_socket.sendall(f"{fecha_fin}\n".encode())

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
    result = [line for line in result if line]
    return result   

def show_results(request, palabra, fecha_inicio, fecha_fin):
    data = send_and_receive_data(palabra, fecha_inicio, fecha_fin)
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

   
    chart_title = f"Análisis de sentimiento de la palabra '{palabra}' entre las fechas {fecha_inicio} y {fecha_fin}"

    context = {
        'chart_title': chart_title,
        'labels': json.dumps(labels),  
        'values': json.dumps(values),  
        'palabra': palabra,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'results.html', context)
