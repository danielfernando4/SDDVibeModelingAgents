# Documento de Requisitos

## Introducción
Este documento detalla los requisitos funcionales y no funcionales para la aplicación de Gestión de Citas Médicas, diseñada para pacientes que buscan una forma sencilla y eficiente de programar, reprogramar y cancelar citas con sus médicos. El objetivo es mejorar la experiencia del usuario y reducir las ausencias a consultas.

## Contexto de Alcance
- **Dentro del alcance**: Gestión de citas médicas (programar, reprogramar y cancelar), envío de recordatorios y notificaciones personalizadas, acceso al historial de citas del paciente, integración con calendarios personales, facturación electrónica para las citas médicas, gestión de prescripciones médicas y gestión de fármacos.
- **Fuera del alcance**: Funcionalidades de telemedicina o consultas virtuales, soporte para múltiples idiomas en la primera versión.

## Requisitos

### Requisito 1: Programación de Citas
**Objetivo:** Como paciente, quiero programar citas médicas de manera intuitiva, para recibir atención médica oportuna.

#### Criterios de Aceptación
1. When el paciente selecciona una fecha y hora disponibles, el sistema shall confirmar la cita programada.
2. If el paciente intenta programar una cita en un horario no disponible, then el sistema shall mostrar un mensaje de error indicando la indisponibilidad.
3. While el paciente está en el proceso de programación, el sistema shall permitir la búsqueda por especialidad médica.
4. Where el paciente ingresa sus datos personales, el sistema shall validar la información antes de confirmar la cita.
5. El sistema shall enviar un correo electrónico de confirmación al paciente una vez que la cita ha sido programada.
6. El sistema shall asegurar que la duración de la cita esté entre 30 minutos y 1 hora.
7. El sistema shall verificar que un médico no tenga más de 6 pacientes programados por día.

### Requisito 2: Reprogramación de Citas
**Objetivo:** Como paciente, quiero reprogramar mis citas médicas, para adaptarlas a mis necesidades.

#### Criterios de Aceptación
1. When el paciente selecciona una cita existente, el sistema shall permitir la opción de reprogramación.
2. If el paciente intenta reprogramar una cita a un horario no disponible, then el sistema shall mostrar un mensaje de error indicando la indisponibilidad.
3. While el paciente está reprogramando, el sistema shall mostrar las citas disponibles en un formato claro y accesible.
4. Where la reprogramación se completa, el sistema shall enviar un nuevo correo electrónico de confirmación al paciente.
5. El sistema shall actualizar el historial de citas del paciente para reflejar la nueva fecha y hora.

### Requisito 3: Cancelación de Citas
**Objetivo:** Como paciente, quiero cancelar mis citas médicas fácilmente, para evitar penalizaciones.

#### Criterios de Aceptación
1. When el paciente selecciona una cita para cancelar, el sistema shall confirmar la acción antes de proceder.
2. If el paciente intenta cancelar una cita que ya ha pasado, then el sistema shall mostrar un mensaje de error indicando que la cita no se puede cancelar.
3. While el paciente está en el proceso de cancelación, el sistema shall ofrecer la opción de reprogramar la cita en lugar de cancelarla.
4. Where la cancelación se completa, el sistema shall enviar un correo electrónico de confirmación al paciente.
5. El sistema shall actualizar el historial de citas del paciente para reflejar la cancelación.

### Requisito 4: Notificaciones Personalizadas
**Objetivo:** Como paciente, quiero recibir recordatorios automáticos sobre mis citas, para no olvidarlas.

#### Criterios de Aceptación
1. When se programa una cita, el sistema shall ofrecer la opción de personalizar el tipo de recordatorio (SMS o notificación push).
2. If el paciente no ha configurado recordatorios, then el sistema shall enviar un recordatorio predeterminado 24 horas antes de la cita.
3. While el paciente modifica sus preferencias de notificación, el sistema shall guardar los cambios de manera efectiva.
4. Where un recordatorio se envía, el sistema shall incluir la fecha, hora y lugar de la cita.
5. El sistema shall permitir al paciente desactivar las notificaciones en cualquier momento.

### Requisito 5: Acceso al Historial de Citas
**Objetivo:** Como paciente, quiero acceder a mi historial de citas, para tener un seguimiento de mi atención médica.

#### Criterios de Aceptación
1. When el paciente accede a la sección de historial de citas, el sistema shall mostrar todas las citas pasadas y futuras.
2. If no hay citas en el historial, then el sistema shall mostrar un mensaje indicando que no hay citas registradas.
3. While el paciente revisa su historial, el sistema shall permitir filtrar las citas por fecha y estado (completadas, canceladas).
4. Where el paciente selecciona una cita del historial, el sistema shall mostrar los detalles de la cita seleccionada.
5. El sistema shall permitir al paciente descargar su historial de citas en formato PDF.

### Requisito 6: Integración con Calendarios
**Objetivo:** Como paciente, quiero sincronizar mis citas con mis calendarios personales, para una gestión más eficiente del tiempo.

#### Criterios de Aceptación
1. When el paciente selecciona la opción de integración con calendarios, el sistema shall ofrecer opciones para sincronizar con Google Calendar e iCal.
2. If el paciente no tiene configurada la integración, then el sistema shall guiarlo a través del proceso de configuración.
3. While la sincronización está activa, el sistema shall actualizar automáticamente el calendario personal del paciente con nuevas citas.
4. Where el paciente cancela o reprograma una cita, el sistema shall reflejar esos cambios en el calendario personal.
5. El sistema shall permitir al paciente desconectar la integración en cualquier momento.

### Requisito 7: Facturación Electrónica
**Objetivo:** Como paciente, quiero recibir mis facturas de manera digital tras la programación o cancelación de una cita, para tener un registro claro de mis gastos.

#### Criterios de Aceptación
1. When se programa una cita, el sistema shall generar automáticamente una factura electrónica y enviarla al correo del paciente.
2. If el paciente cancela una cita, then el sistema shall enviar una factura electrónica que refleje la cancelación y cualquier cargo aplicable.
3. While el paciente revisa sus citas, el sistema shall permitirle acceder a sus facturas electrónicas desde su historial.
4. Where se genera una factura, el sistema shall incluir detalles como la fecha, hora, médico y costo de la cita.
5. El sistema shall permitir al paciente descargar sus facturas electrónicas en formato PDF.

### Requisito 8: Gestión de Prescripciones Médicas
**Objetivo:** Como médico, quiero poder gestionar las prescripciones médicas de mis pacientes, para asegurar un seguimiento adecuado de su tratamiento.

#### Criterios de Aceptación
1. When el médico crea una prescripción, el sistema shall permitirle ingresar detalles como el nombre del medicamento, dosis y duración del tratamiento.
2. If el médico intenta prescribir un medicamento no disponible, then el sistema shall mostrar un mensaje de error indicando la indisponibilidad.
3. While el médico revisa las prescripciones, el sistema shall permitirle editar o eliminar prescripciones existentes.
4. Where se guarda una prescripción, el sistema shall notificar al paciente sobre la nueva prescripción a través de un correo electrónico.
5. El sistema shall permitir al médico acceder al historial de prescripciones de cada paciente.

### Requisito 9: Gestión de Fármacos
**Objetivo:** Como paciente, quiero tener acceso a información sobre los fármacos prescritos, para entender mejor mi tratamiento.

#### Criterios de Aceptación
1. When el paciente accede a su historial de prescripciones, el sistema shall mostrar información detallada sobre cada fármaco.
2. If el paciente selecciona un fármaco, then el sistema shall proporcionar información adicional como efectos secundarios y contraindicaciones.
3. While el paciente revisa sus fármacos, el sistema shall permitirle marcar los medicamentos que ha tomado.
4. Where se actualiza una prescripción, el sistema shall notificar al paciente sobre los cambios realizados.
5. El sistema shall permitir al paciente buscar información sobre fármacos en una base de datos integrada.

### Requisito 10: Seguridad de Datos
**Objetivo:** Como usuario, quiero que mis datos personales estén protegidos, para garantizar mi privacidad.

#### Criterios de Aceptación
1. When el paciente ingresa sus datos, el sistema shall cifrar la información antes de almacenarla.
2. If se detecta un intento de acceso no autorizado, then el sistema shall bloquear el acceso y notificar al administrador.
3. While el paciente utiliza la aplicación, el sistema shall requerir autenticación para acceder a información sensible.
4. Where se realiza una transacción de datos, el sistema shall utilizar protocolos de seguridad estándar (como HTTPS).
5. El sistema shall cumplir con las normativas de protección de datos personales vigentes.

### Requisito 11: Rendimiento
**Objetivo:** Como usuario, quiero que la aplicación funcione de manera rápida y eficiente, para una mejor experiencia.

#### Criterios de Aceptación
1. When el paciente realiza una acción (programar, reprogramar, cancelar), el sistema shall completar la acción en menos de 3 segundos.
2. If el sistema experimenta una carga alta, then el rendimiento no deberá degradarse más del 20%.
3. While el paciente navega por la aplicación, el sistema shall mantener una tasa de respuesta de al menos 95%.
4. Where se accede a la aplicación, el sistema shall cargar la interfaz principal en menos de 5 segundos.
5. El sistema shall ser capaz de manejar al menos 1000 usuarios simultáneamente sin pérdida de rendimiento.

### Requisito 12: Usabilidad
**Objetivo:** Como usuario, quiero que la aplicación sea fácil de usar, para que pueda gestionar mis citas sin complicaciones.

#### Criterios de Aceptación
1. When el paciente accede a la aplicación, el sistema shall presentar una interfaz intuitiva y amigable.
2. If el paciente no entiende una función, then el sistema shall proporcionar ayuda contextual accesible.
3. While el paciente navega por la aplicación, el sistema shall permitir la navegación fluida entre las diferentes secciones.
4. Where se realicen cambios en la interfaz, el sistema shall notificar a los usuarios sobre las actualizaciones significativas.
5. El sistema shall incluir un tutorial inicial para nuevos usuarios que explique las funcionalidades clave.

Este documento establece los requisitos necesarios para el desarrollo de la aplicación de Gestión de Citas Médicas, asegurando que se aborden tanto las funcionalidades requeridas como los aspectos no funcionales que garantizan una experiencia de usuario óptima.