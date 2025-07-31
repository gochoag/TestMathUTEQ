from django.core.management.base import BaseCommand
from quizzes.models import Evaluacion, Pregunta, Opcion, Participantes, ResultadoEvaluacion
from decimal import Decimal

class Command(BaseCommand):
    help = 'Prueba la nueva lógica de puntuación con ejemplos'

    def handle(self, *args, **options):
        self.stdout.write('=== PRUEBA DE NUEVA LÓGICA DE PUNTUACIÓN ===')
        
        # Ejemplos de puntuación según la nueva lógica
        self.stdout.write('\n=== EJEMPLOS DE PUNTUACIÓN ===')
        self.stdout.write('Preguntas mostradas: 20')
        self.stdout.write('Puntuación máxima: 20 correctas = 20 puntos = 10.000/10')
        
        # Ejemplo 1: 20 correctas
        correctas = 20
        incorrectas = 0
        sin_responder = 0
        puntos = correctas - (incorrectas * 0.25)
        ponderado = (puntos / 20) * 10
        self.stdout.write(f'\nEjemplo 1: {correctas} correctas, {incorrectas} incorrectas, {sin_responder} sin responder')
        self.stdout.write(f'  Cálculo: {correctas} - ({incorrectas} × 0.25) = {puntos} puntos')
        self.stdout.write(f'  Ponderado: ({puntos}/20) × 10 = {ponderado:.3f}/10')
        
        # Ejemplo 2: 17 correctas, 2 incorrectas, 1 sin responder
        correctas = 17
        incorrectas = 2
        sin_responder = 1
        puntos = correctas - (incorrectas * 0.25)
        ponderado = (puntos / 20) * 10
        self.stdout.write(f'\nEjemplo 2: {correctas} correctas, {incorrectas} incorrectas, {sin_responder} sin responder')
        self.stdout.write(f'  Cálculo: {correctas} - ({incorrectas} × 0.25) = {puntos} puntos')
        self.stdout.write(f'  Ponderado: ({puntos}/20) × 10 = {ponderado:.3f}/10')
        
        # Ejemplo 3: 15 correctas, 5 incorrectas, 0 sin responder
        correctas = 15
        incorrectas = 5
        sin_responder = 0
        puntos = correctas - (incorrectas * 0.25)
        ponderado = (puntos / 20) * 10
        self.stdout.write(f'\nEjemplo 3: {correctas} correctas, {incorrectas} incorrectas, {sin_responder} sin responder')
        self.stdout.write(f'  Cálculo: {correctas} - ({incorrectas} × 0.25) = {puntos} puntos')
        self.stdout.write(f'  Ponderado: ({puntos}/20) × 10 = {ponderado:.3f}/10')
        
        # Ejemplo 4: 10 correctas, 10 incorrectas, 0 sin responder
        correctas = 10
        incorrectas = 10
        sin_responder = 0
        puntos = correctas - (incorrectas * 0.25)
        ponderado = (puntos / 20) * 10
        self.stdout.write(f'\nEjemplo 4: {correctas} correctas, {incorrectas} incorrectas, {sin_responder} sin responder')
        self.stdout.write(f'  Cálculo: {correctas} - ({incorrectas} × 0.25) = {puntos} puntos')
        self.stdout.write(f'  Ponderado: ({puntos}/20) × 10 = {ponderado:.3f}/10')
        
        # Ejemplo 5: 0 correctas, 20 incorrectas, 0 sin responder
        correctas = 0
        incorrectas = 20
        sin_responder = 0
        puntos = correctas - (incorrectas * 0.25)
        ponderado = max(0, (puntos / 20) * 10)  # No puede ser negativo
        self.stdout.write(f'\nEjemplo 5: {correctas} correctas, {incorrectas} incorrectas, {sin_responder} sin responder')
        self.stdout.write(f'  Cálculo: {correctas} - ({incorrectas} × 0.25) = {puntos} puntos')
        self.stdout.write(f'  Ponderado: max(0, ({puntos}/20) × 10) = {ponderado:.3f}/10')
        
        # Verificar resultados existentes
        self.stdout.write('\n=== VERIFICACIÓN DE RESULTADOS EXISTENTES ===')
        resultados = ResultadoEvaluacion.objects.filter(completada=True)[:10]
        
        if resultados.exists():
            self.stdout.write(f'Mostrando los primeros {resultados.count()} resultados:')
            for resultado in resultados:
                self.stdout.write(f'  {resultado.participante.NombresCompletos}: {resultado.get_puntaje_numerico()} ({resultado.puntaje:.1f}%)')
        else:
            self.stdout.write('No hay resultados para verificar')
        
        self.stdout.write('\n=== FIN DE PRUEBA ===') 