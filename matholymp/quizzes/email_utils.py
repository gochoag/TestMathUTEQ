"""
Utilidades para el envío de correos electrónicos
"""

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
    
    if email_type == 'credentials':
        # Mensaje en texto plano para credenciales
        plain_message = f"""
        Estimado/a {nombre},

        Sus credenciales de acceso al {system_name} son las siguientes:

        Usuario: {username}
        Contraseña: {nueva_password}

        Puede acceder al sistema usando estas credenciales.

        Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos.

        Saludos cordiales,
        CARRERA DE INGENIERIA MECÁNICA
                """
        
        # Mensaje HTML moderno para credenciales
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Credenciales de Acceso</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                
                .header h1 {{
                    font-size: 28px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                
                .header .subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 25px;
                    color: #555;
                }}
                
                .credentials-card {{
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 12px;
                    padding: 25px;
                    margin: 25px 0;
                    border-left: 5px solid #667eea;
                }}
                
                .credentials-card h3 {{
                    color: #667eea;
                    font-size: 20px;
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
                    font-size: 16px;
                    min-width: 120px;
                }}
                
                .credential-value {{
                    background: white;
                    padding: 8px 15px;
                    border-radius: 8px;
                    font-family: 'Courier New', monospace;
                    font-weight: 600;
                    color: #667eea;
                    border: 2px solid #e0e0e0;
                    font-size: 14px;
                    flex: 1;
                    margin-left: 15px;
                    text-align: center;
                }}
                
                .info-box {{
                    background: #e3f2fd;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #2196f3;
                }}
                
                .info-box h4 {{
                    color: #1976d2;
                    margin-bottom: 10px;
                    font-size: 16px;
                }}
                
                .info-box p {{
                    color: #424242;
                    font-size: 14px;
                }}
                
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e0e0e0;
                }}
                
                .footer p {{
                    color: #666;
                    font-size: 14px;
                }}
                
                .footer .signature {{
                    font-weight: 600;
                    color: #667eea;
                    margin-top: 10px;
                }}
                
                .logo {{
                    font-size: 20px;
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
                    <div class="logo">🏆 OLIMPIADA INTERCOLEGIAL DE MATEMATICA, UTEQ-2025</div>
                    <h1>Credenciales de Acceso</h1>
                    <div class="subtitle">{system_name}</div>
                </div>
                
                <div class="content">
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
                    
                    <div class="info-box">
                        <h4>Información Importante</h4>
                        <p>• Guarde estas credenciales en un lugar seguro<br>
                        • No comparta su contraseña con otras personas<br>
                        • Puede cambiar su contraseña una vez que ingrese al sistema</p>
                    </div>
                    
                    <p>Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos. 
                    Estamos aquí para ayudarle.</p>
                </div>
                
                <div class="footer">
                    <p>Saludos cordiales,</p>
                    <div class="signature">CARRERA DE INGENIERIA MECÁNICA</div>
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

        Si tiene alguna pregunta o necesita información adicional, no dude en contactarnos.

        Saludos cordiales,
        CARRERA DE INGENIERIA MECÁNICA
                """
        
        # Mensaje HTML moderno para lista de participantes
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Lista de Participantes</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                }}
                
                .email-container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                
                .header h1 {{
                    font-size: 28px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
                
                .header .subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 25px;
                    color: #555;
                }}
                
                .participants-table {{
                    margin: 30px 0;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                
                .participants-table table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                }}
                
                .participants-table th {{
                    background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
                    color: white;
                    padding: 15px 10px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                .participants-table td {{
                    padding: 12px 10px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 13px;
                }}
                
                .participants-table tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                
                .participants-table tr:hover {{
                    background-color: #e3f2fd;
                }}
                
                .info-box {{
                    background: #fff3cd;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                    border-left: 4px solid #ffc107;
                }}
                
                .info-box h4 {{
                    color: #856404;
                    margin-bottom: 10px;
                    font-size: 16px;
                }}
                
                .info-box ul {{
                    color: #856404;
                    font-size: 14px;
                    padding-left: 20px;
                }}
                
                .info-box li {{
                    margin-bottom: 8px;
                }}
                
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e0e0e0;
                }}
                
                .footer p {{
                    color: #666;
                    font-size: 14px;
                }}
                
                .footer .signature {{
                    font-weight: 600;
                    color: #667eea;
                    margin-top: 10px;
                }}
                
                .logo {{
                    font-size: 20px;
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
                    <div class="logo">🏆 OLIMPIADA INTERCOLEGIAL DE MATEMATICA, UTEQ-2025</div>
                    <h1>Lista de Participantes</h1>
                    <div class="subtitle">Grupo: {system_name}</div>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Estimado/a <strong>{nombre}</strong>,
                    </div>
                    
                    <p>Adjunto encontrará la lista completa de participantes asignados al grupo <strong>"{system_name}"</strong>.</p>
                    
                    <div class="participants-table">
                        {additional_content.get('participantes_html', '')}
                    </div>
                    
                    <div class="info-box">
                        <h4>Información Importante</h4>
                        <ul>
                            <li><strong>Total de participantes:</strong> {additional_content.get('total_participantes', 'N/A')}</li>
                            <li><strong>IMPORTANTE:</strong> Las contraseñas mostradas en la tabla son las credenciales actuales de los participantes.</li>
                            <li>Los participantes pueden acceder a la plataforma usando su <strong>cédula como usuario</strong> y la <strong>contraseña que aparece en la tabla</strong>.</li>
                            <li>Estas son las contraseñas que los participantes deben usar para acceder al sistema.</li>
                        </ul>
                    </div>
                    
                    <p>Si tiene alguna pregunta o necesita información adicional, no dude en contactarnos. 
                    Estamos aquí para ayudarle.</p>
                </div>
                
                <div class="footer">
                    <p>Saludos cordiales,</p>
                    <div class="signature">CARRERA DE INGENIERIA MECÁNICA</div>
                    <p style="margin-top: 15px; font-size: 12px; color: #999;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    return plain_message, html_message 