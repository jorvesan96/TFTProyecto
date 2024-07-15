from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

import socket
import json

ip_addresses = ["172.26.253.22", "172.26.253.23"]
last_used_ip_index = 0

def index(request):
    return render(request, 'index.html')

def process_request(request):
    if request.method == 'POST':
        palabra = request.POST.get('palabra')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        if palabra and fecha_inicio and fecha_fin:
            return redirect('results', palabra=palabra, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        else:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

    return JsonResponse({'error': 'This endpoint only accepts POST requests.'}, status=405)

def send_and_receive_data(flag, palabra=None, fecha_inicio=None, fecha_fin=None):
    global last_used_ip_index
    result = []
    connected = False
    
    for attempt in range(len(ip_addresses)):
        ip = ip_addresses[last_used_ip_index]
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            print(f"Attempting to connect to {ip}...")
            client_socket.connect((ip, 9999))
            print("Socket connected to", ip)
            print("Sending data to the socket...")
            client_socket.sendall(f"{flag}\n".encode())

            if flag == 0:
                client_socket.sendall(f"{palabra}\n".encode())
                client_socket.sendall(f"{fecha_inicio}\n".encode())
                client_socket.sendall(f"{fecha_fin}\n".encode())
            elif flag == 1:
                pass
            result = receive_data(client_socket)
            connected = True
            break
        except Exception as e:
            print(f"Error connecting to {ip}: {str(e)}")
            last_used_ip_index = (last_used_ip_index + 1) % len(ip_addresses)

    if not connected:
        print("No se pudo conectar a ninguna de las direcciones IP especificadas.")

    return result

def receive_data(client_socket):
    result = []
    buffer = ''
    try:
        print("Receiving data from the socket...")
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            buffer += data.decode()
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                result.append(line.strip())
        print("Data received.")
    except Exception as e:
        print(f"Error al recibir datos del socket: {str(e)}")
    return result

def show_results(request, palabra, fecha_inicio, fecha_fin):
    data = send_and_receive_data(0, palabra=palabra, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    print("Datos recibidos del servidor socket pedidos por el cliente:", data)
    
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
        
        data = send_and_receive_data(1)

        print("Datos recibidos del servidor socket pedidos por el cliente:", data)
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
        print(f"Error en la función show_word_cloud_results: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def polling_endpoint_results(request):
    print("Datos recibidos del servidor socket automaticamente:")
    palabra = request.GET.get('palabra', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    data = send_and_receive_data(0, palabra=palabra, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    print(data)
    return JsonResponse({'data': data})

def polling_endpoint_word_cloud(request):
    print("Datos recibidos del servidor socket automaticamente:")
    data = send_and_receive_data(1)
    print(data)
    return JsonResponse({'data': data})

