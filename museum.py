    def do_scale_image(self, scroll_value, cursor_pivot=True, override_factor=None):

        if not self.transformations_allowed:
            return

        if not override_factor:
            self.region_zoom_in_cancel()

        if self.image_scale >= self.UPPER_SCALE_LIMIT-0.001:
            if scroll_value > 0.0:
                return

        if self.image_scale <= self.LOWER_SCALE_LIMIT:
            if scroll_value < 0.0:
                return

        animated_zoom_enabled = self.isAnimationEffectsAllowed() and self.STNG_animated_zoom

        before_scale = self.image_scale

        # эти значения должны быть вычислены до изменения self.image_scale
        r = self.get_image_viewport_rect()
        current_image_rect = QRectF(r)
        p1 = r.topLeft()
        p2 = r.bottomRight()

        t = self.get_secret_hint_rect()
        t1 = t.topLeft()
        t2 = t.bottomRight()

        if not override_factor:

            if self.STNG_legacy_image_scaling:
                # старый глючный метод со скачками зума, но зато работает уже очень долго

                if self.image_scale > 1.0: # если масштаб больше нормального
                    factor = self.image_scale/self.UPPER_SCALE_LIMIT
                    if scroll_value < 0.0:
                        self.image_scale -= 0.1 + 8.5*factor #0.2
                    else:
                        self.image_scale += 0.1 + 8.5*factor #0.2

                else: # если масштаб меньше нормального
                    if scroll_value < 0.0:
                        self.image_scale -= 0.05 #0.1
                    else:
                        self.image_scale += 0.05 #0.1

            else:
                # Здесь надо задавать image_scale в зависимости от
                # новой ширины или длины картинки, высчитаннной в процентах
                # от старой длины или ширины.
                # Дельта колеса мыши будет определять лишь уменьшение или увеличение

                _pixmap_rect = self.get_rotated_pixmap().rect()
                _viewport_rect = self.get_image_viewport_rect()
                viewport_width = _viewport_rect.width()
                _height = _viewport_rect.height()

                # чем больше scale_speed, тем больше придётся крутить колесо мыши
                # для одной и той же величины увеличения или уменьшения
                if animated_zoom_enabled:
                    gen = self.get_current_animation_task_generation(anim_id="zoom")
                    scale_speed = 2.5
                    scale_speed -= 1.4*(min(20, gen)/20)
                    # msg = f'zoom generation: {gen}, result speed value: {scale_speed}'
                    # print(msg)
                else:
                    scale_speed = 5

                if scroll_value < 0.0:
                    _new_width = viewport_width*(scale_speed-1)/scale_speed
                    self.image_scale = _new_width/_pixmap_rect.width()
                else:
                    _new_width = viewport_width*scale_speed/(scale_speed-1)
                    # предохранитель от залипания
                    if _new_width - float(viewport_width) < 10.0:
                        _new_width = float(viewport_width) + 10.0
                    self.image_scale = _new_width/_pixmap_rect.width()



        self.image_scale = min(max(self.LOWER_SCALE_LIMIT, self.image_scale),
                                                                    self.UPPER_SCALE_LIMIT)
        delta = before_scale - self.image_scale


        clamped = False
        if (before_scale < 1.0 and self.image_scale > 1.0) or (before_scale > 1.0 and self.image_scale < 1.0):
            print("scale is clamped to 100%")
            self.image_scale = 1.0
            clamped = True

        pixmap_rect = self.get_rotated_pixmap().rect()
        orig_width = pixmap_rect.width()
        orig_height = pixmap_rect.height()

        if override_factor:
            pivot = QPointF(self.rect().center())
        else:
            if cursor_pivot:
                if r.contains(self.mapped_cursor_pos()):
                    pivot = QPointF(self.mapped_cursor_pos())
                else:
                    pivot = QPointF(self.rect().center())
            else:
                pivot = QPointF(self.image_center_position)

        p1 = p1 - pivot
        p2 = p2 - pivot
        t1 = t1 - pivot
        t2 = t2 - pivot

        if False:
            factor = (1.0 - delta)
            # delta  -->  factor
            #  -0.1  -->  1.1: больше 1.0
            #  -0.2  -->  1.2: больше 1.0
            #   0.2  -->  0.8: меньше 1.0
            #   0.1  -->  0.9: меньше 1.0
            # Единственный недостаток factor = (1.0 - delta) в том,
            # что он увеличивает намного больше, чем должен:
            # из-за этого постоянно по факту превышается UPPER_SCALE_LIMIT.
            # Вариант ниже как раз призван устранить этот недостаток.
            # Хотя прелесть factor = (1.0 - delta) в том,
            # что не нужно создавать хитровыебанные дельты с множителями,
            # как это сделано чуть выше.
        else:
            # x от p2 будет всегда больше, чем x от p1 в силу того,
            # что p1 это верхний левый угол прямоугольника, а p2 это нижний правый угол того же прямоугольника,
            # и начало системы координат всегда находится ближе к p1
            current_width = abs(p2.x() - p1.x())
            # предохранитель на всякий случай
            current_width = max(1.0, current_width)

            # Переменную factor стоило бы называть delta_factor,
            # потому что увеличение или уменьшение масштаба всегда идёт от текущего значения масштабирования;
            # здесь image_scale содержит уже новое значение;
            factor = 1.0 - (before_scale - self.image_scale)*orig_width/current_width
            # переменная factor используется как множитель. Если множитель больше 1.0, то будет увеличение,
            # а если меньше 1.0 и не меньше, и не равен 0.0, то будет уменьшение.
            # 1.0 в начале выражения выстален именно для того, чтобы определить начальное значение,
            # которое либо уменьшается стремясь к 0.0, либо увеличивается до бесконечности.
            # Но как правило, благодаря print(factor) удалось узнать, что
            # в factor оказываются только значения 1.6 и 0.6 для увеличения и уменьшения соответственно
            # и проще можно было бы написать
            # if scroll_value > 0:
            #     factor = 1.6
            # else:
            #     factor = 0.6
            # главное чтобы эти значения были обратными друг другу. И наверно так и стоило написать,
            # но в самом начале разработки, торопясь, я изменял image_scale напрямую,
            # а не задавал image_scale как отношение новой длины к старой длине,
            # отсюда и ненужные усложнения в коде

            if Globals.DEBUG:
                scale_delta_factor = factor
                print(f'scale_delta_factor = {scale_delta_factor:.2f}')

        if override_factor:
            factor = override_factor

        p1 = QPointF(p1.x()*factor, p1.y()*factor)
        p2 = QPointF(p2.x()*factor, p2.y()*factor)
        t1 = QPointF(t1.x()*factor, t1.y()*factor)
        t2 = QPointF(t2.x()*factor, t2.y()*factor)

        p1 = p1 + pivot
        p2 = p2 + pivot
        t1 = t1 + pivot
        t2 = t2 + pivot

        # здесь задаём размер и положение
        new_width = abs(p2.x() - p1.x())
        new_height = abs(p2.y() - p1.y())

        if clamped:
            # здесь приходится задавать явно,
            # иначе масштабирование может застрять на этом значении
            # при уменьшении или при увеличении; Это конечно костыль,
            # и всю функцию надо будет переписать в скором времени
            image_scale = 1.0
        else:
            image_scale = new_width / orig_width
        image_center_position = (p1 + p2)/2

        # end
        if override_factor:
            return image_scale, image_center_position.toPoint()
        else:

            if animated_zoom_enabled:

                def update_function():
                    self.image_scale = self.image_rect.width()/self.get_rotated_pixmap().width()
                    icp = QPointF(self.image_rect.center()) + self.translation_delta_when_animation
                    self.image_center_position = icp
                    self.update()

                def on_start():
                    self.translation_delta_when_animation = QPointF(0, 0)

                def on_finish():
                    pass


                wanna_image_rect = self.get_image_viewport_rect(od=(image_center_position, image_scale))
                self.animate_properties(
                    [
                        (self, "image_rect", current_image_rect, wanna_image_rect, update_function),
                    ],
                    anim_id="zoom",
                    duration=0.7,
                    # easing=QEasingCurve.OutQuad
                    # easing=QEasingCurve.OutQuart
                    # easing=QEasingCurve.OutQuint
                    easing=QEasingCurve.OutCubic,
                    callback_on_start=on_start,
                    callback_on_finish=on_finish,
                )

            else:

                if self.image_scale == 100.0 and image_scale < 100.0 and scroll_value > 0.0:
                    # Предохранитель от постепенного заплыва картинки в сторону верхнего левого угла
                    # из-за кручения колеса мыши в область ещё большего увеличения
                    # Так происходит, потому что переменная image_scale при этом чуть меньше 100.0
                    pass
                else:
                    self.image_scale = image_scale

                viewport_rect = self.get_image_viewport_rect()
                is_vr_small = viewport_rect.width() < 150 or viewport_rect.height() < 150
                if before_scale < self.image_scale and is_vr_small:
                    self.image_center_position = QPoint(QCursor().pos())
                else:
                    self.image_center_position = image_center_position.toPoint()

                self.hint_center_position = ((t1 + t2)/2).toPoint()

        self.show_center_label(self.label_type.SCALE)

        self.activate_or_reset_secret_hint()

        self.update()
