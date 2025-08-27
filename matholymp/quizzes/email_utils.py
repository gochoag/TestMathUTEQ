"""
Utilidades para el envío de correos electrónicos
"""

import datetime

def generate_email_messages(subject, nombre, system_name, username, nueva_password, email_type='credentials', additional_content=None):
    """
    Función global para generar mensajes de correo electrónico en formato texto plano y HTML.
    
    Args:
        subject (str): Asunto del correo
        nombre (str): Nombre del destinatario
        system_name (str): Nombre del sistema
        username (str): Nombre de usuario
        nueva_password (str): Contraseña generada
        email_type (str): Tipo de correo ('credentials' o 'participants_list')
        additional_content (dict): Contenido adicional (para listas de participantes)
    
    Returns:
        tuple: (plain_message, html_message)
    """
    
    # Obtener el año actual
    current_year = datetime.datetime.now().year
    
    if email_type == 'credentials':
        # Mensaje en texto plano para credenciales
        plain_message = f"""
        Estimado/a {nombre},

        Sus credenciales de acceso al {system_name} son las siguientes:

        Usuario: {username}
        Contraseña: {nueva_password}

        Puede acceder al sistema usando estas credenciales.

        Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos al correo: olimpiadasmecanicauteq@gmail.com

        Atentamente,
        Carrera de Ingeniería Mecánica
        Universidad Técnica Estatal Quevedo
                """
        
        # Mensaje HTML moderno para credenciales
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
            <title>Credenciales de Acceso</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Open Sans', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f4f4f4;
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    overflow: hidden;
                    border: 1px solid #ddd;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #025a27 0%, #034a2a 100%);
                    color: white;
                    padding: 30px 30px;
                    text-align: center;
                    position: relative;
                }}
                
                .header::after {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
                }}
                
                .header h1 {{
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0 0 10px 0;
                    letter-spacing: 0.5px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .header h2 {{
                    font-size: 18px;
                    font-weight: 400;
                    margin: 0;
                    letter-spacing: 0.3px;
                    opacity: 0.95;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 16px;
                    margin-bottom: 25px;
                    color: #555;
                    font-weight: 400;
                }}
                
                .credentials-card {{
                    background: #f9f9f9;
                    border-radius: 8px;
                    padding: 25px;
                    margin: 25px 0;
                    border-left: 4px solid #025a27;
                }}
                
                .credentials-card h3 {{
                    color: #025a27;
                    font-size: 18px;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                
                .credential-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}
                
                .credential-item:last-child {{
                    border-bottom: none;
                }}
                
                .credential-label {{
                    font-weight: 600;
                    color: #555;
                    font-size: 14px;
                    min-width: 120px;
                }}
                
                .credential-value {{
                    background: #fff;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    font-weight: 600;
                    color: #025a27;
                    border: 1px solid #ddd;
                    font-size: 14px;
                    flex: 1;
                    margin-left: 15px;
                    text-align: center;
                }}
                
                .info-box {{
                    background: #e8f5e8;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #025a27;
                }}
                
                .info-box h4 {{
                    color: #025a27;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: 600;
                }}
                
                .info-box p {{
                    color: #424242;
                    font-size: 14px;
                    font-weight: 400;
                }}
                
                .footer {{
                    background: #f4f4f4;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #ddd;
                }}
                
                .footer p {{
                    color: #666;
                    font-size: 14px;
                    font-weight: 400;
                }}
                
                .footer .signature {{
                    font-weight: 600;
                    color: #025a27;
                    margin-top: 10px;
                }}
                
                .logo {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    line-height: 1.3;
                }}
                
                @media (max-width: 600px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .content {{
                        padding: 20px 15px;
                    }}
                    
                    .header {{
                        padding: 20px;
                    }}
                    
                    .credential-item {{
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 8px;
                    }}
                    
                    .credential-value {{
                        margin-left: 0;
                        width: 100%;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>Universidad Técnica Estatal de Quevedo</h1>
                    <h2>Olimpiada Intercolegial de Matemática {current_year}</h2>
                </div>
                
                <div class="content">
                    <h1 style="font-size: 28px; font-weight: 700; color: #025a27; text-align: center; margin-bottom: 10px;">Credenciales de Acceso</h1>
                    <div class="subtitle" style="font-size: 18px; color: #555; text-align: center; margin-bottom: 30px;">{system_name}</div>
                    
                    <div class="greeting">
                        Estimado/a <strong>{nombre}</strong>,
                    </div>
                    
                    <p>Hemos generado sus credenciales de acceso al <strong>{system_name}</strong>. 
                    A continuación encontrará la información necesaria para ingresar al sistema:</p>
                    
                    <div class="credentials-card">
                        <h3>Sus Credenciales</h3>
                        <div class="credential-item">
                            <span class="credential-label">Usuario:</span>
                            <span class="credential-value">{username}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Contraseña:</span>
                            <span class="credential-value">{nueva_password}</span>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://aplicaciones.uteq.edu.ec:9051/login/" style="background: #025a27; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: 600; font-size: 16px;">Acceder al Sistema</a>
                    </div>
                    
                    <div class="info-box">
                        <h4>Información Importante</h4>
                        <p>• Guarde estas credenciales en un lugar seguro<br>
                        • No comparta su contraseña con otras personas<br>
                        • Puede cambiar su contraseña una vez que ingrese al sistema<br>
                        • Para soporte técnico, contacte: <a href="mailto:olimpiadasmecanicauteq@gmail.com" style="color: #025a27;">olimpiadasmecanicauteq@gmail.com</a></p>
                    </div>
                    
                    <p>Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos. 
                    Estamos aquí para ayudarle.</p>
                </div>
                
                <div class="footer">
                    <p>Atentamente,</p>
                    <div class="signature">Carrera de Ingeniería Mecánica<br>Universidad Técnica Estatal Quevedo</div>
                    <p style="margin-top: 15px; font-size: 12px; color: #999;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
    elif email_type == 'participants_list':
        # Mensaje en texto plano para lista de participantes
        plain_message = f"""
        Estimado/a {nombre},

        Adjunto encontrará la lista completa de participantes asignados al grupo "{system_name}".

        Total de participantes: {additional_content.get('total_participantes', 'N/A')}

        IMPORTANTE: Las contraseñas mostradas en la tabla son las credenciales actuales de los participantes.
        Los participantes pueden acceder a la plataforma usando su cédula como usuario y la contraseña que aparece en la tabla.

        Si tiene alguna pregunta o necesita información adicional, no dude en contactarnos al correo: olimpiadasmecanicauteq@gmail.com

        Atentamente,
        Carrera de Ingeniería Mecánica
        Universidad Técnica Estatal Quevedo
                """
        
        # Mensaje HTML moderno para lista de participantes
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
            <title>Lista de Participantes</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Open Sans', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f4f4f4;
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    overflow: hidden;
                    border: 1px solid #ddd;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #025a27 0%, #034a2a 100%);
                    color: white;
                    padding: 30px 30px;
                    text-align: center;
                    position: relative;
                }}
                
                .header::after {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #ffd700 0%, #ffed4e 50%, #ffd700 100%);
                }}
                
                .header h1 {{
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0 0 10px 0;
                    letter-spacing: 0.5px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .header h2 {{
                    font-size: 18px;
                    font-weight: 400;
                    margin: 0;
                    letter-spacing: 0.3px;
                    opacity: 0.95;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 16px;
                    margin-bottom: 25px;
                    color: #555;
                    font-weight: 400;
                }}
                
                .participants-table {{
                    margin: 30px 0;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    border: 2px solid #025a27;
                }}
                
                .participants-table table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                }}
                
                .participants-table th {{
                    background: #025a27;
                    color: white;
                    padding: 15px 10px;
                    text-align: left;
                    font-weight: 700;
                    font-size: 14px;
                    border-bottom: 2px solid #ddd;
                }}
                
                .participants-table td {{
                    padding: 12px 10px;
                    border-bottom: 1px solid #ddd;
                    font-size: 13px;
                    border-right: 1px solid #eee;
                }}
                
                .participants-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                
                .participants-table tr:hover {{
                    background-color: #e8f4fd;
                }}
                
                .info-box {{
                    background: #e8f5e8;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #025a27;
                }}
                
                .info-box h4 {{
                    color: #025a27;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: 600;
                }}
                
                .info-box ul {{
                    color: #025a27;
                    font-size: 14px;
                    padding-left: 20px;
                }}
                
                .info-box li {{
                    margin-bottom: 8px;
                }}
                
                .footer {{
                    background: #f4f4f4;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #ddd;
                }}
                
                .footer p {{
                    color: #666;
                    font-size: 14px;
                    font-weight: 400;
                }}
                
                .footer .signature {{
                    font-weight: 600;
                    color: #025a27;
                    margin-top: 10px;
                }}
                
                .logo {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    line-height: 1.3;
                }}
                
                @media (max-width: 600px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .content {{
                        padding: 20px 15px;
                    }}
                    
                    .header {{
                        padding: 20px;
                    }}
                    
                    .participants-table {{
                        font-size: 12px;
                    }}
                    
                    .participants-table th,
                    .participants-table td {{
                        padding: 8px 5px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>Universidad Técnica Estatal de Quevedo</h1>
                    <h2>Olimpiada Intercolegial de Matemática {current_year}</h2>
                </div>
                
                <div class="content">
                    <h1 style="font-size: 28px; font-weight: 700; color: #025a27; text-align: center; margin-bottom: 10px;">Lista de Participantes</h1>
                    <div class="subtitle" style="font-size: 18px; color: #555; text-align: center; margin-bottom: 30px;">Grupo: {system_name}</div>
                    
                    <div class="greeting">
                        Estimado/a <strong>{nombre}</strong>,
                    </div>
                    
                    <p>Adjunto encontrará la lista completa de participantes asignados al grupo <strong>"{system_name}"</strong>.</p>
                    
                    <div class="participants-table">
                        {additional_content.get('participantes_html', '')}
                    </div>
                    
                    <div class="info-box">
                        <h4>Información</h4>
                        <ul>
                            <li><strong>Total de participantes:</strong> {additional_content.get('total_participantes', 'N/A')}</li>
                            <li><strong>IMPORTANTE:</strong> Las contraseñas mostradas en la tabla son las credenciales actuales de los participantes.</li>
                            <li>Los participantes pueden acceder a la plataforma usando su <strong>cédula como usuario</strong> y la <strong>contraseña que aparece en la tabla</strong>.</li>
                            <li>Para soporte técnico, contacte: <a href="mailto:olimpiadasmecanicauteq@gmail.com" style="color: #025a27;">olimpiadasmecanicauteq@gmail.com</a></li>
                        </ul>
                    </div>
                    
                    <p>Si tiene alguna pregunta o necesita información adicional, no dude en contactarnos. 
                    Estamos aquí para ayudarle.</p>
                </div>
                
                <div class="footer">
                    <p>Atentamente,</p>
                    <div class="signature">Carrera de Ingeniería Mecánica<br>Universidad Técnica Estatal Quevedo</div>
                    <p style="margin-top: 15px; font-size: 12px; color: #999;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return plain_message, html_message 