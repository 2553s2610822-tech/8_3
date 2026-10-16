from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Task:
    name: str
    duration: int
    importance: int
    deadline: Optional[datetime] = None


@dataclass
class Event:
    name: str
    start: datetime
    end: datetime
    kind: str = "일정"


def parse_time(day, time_text):
    """날짜와 시각을 datetime으로 변환한다."""
    return datetime.strptime(
        f"{day} {time_text}", "%Y-%m-%d %H:%M"
    )


def get_priority(task, now, day_end):
    """중요도, 마감 임박도, 예상 소요 시간을 고려한 점수."""
    score = task.importance * 10

    if task.deadline:
        remaining = (
            task.deadline - now
        ).total_seconds() / 3600

        if remaining <= 0:
            score += 100       # 마감이 지났거나 임박
        elif remaining <= 3:
            score += 40
        elif remaining <= 12:
            score += 25
        elif remaining <= 24:
            score += 15
        elif remaining <= 72:
            score += 5

    # 짧은 작업은 일정 사이에 배치하기 쉽다.
    score += max(0, 10 - task.duration / 10)

    return score


def get_reason(task, now):
    reasons = []

    if task.importance >= 5:
        reasons.append("중요도가 높아 우선 배정")

    if task.deadline:
        hours = (task.deadline - now).total_seconds() / 3600

        if hours <= 0:
            reasons.append("마감 시간이 지났으므로 긴급 처리 필요")
        elif hours <= 3:
            reasons.append("마감이 3시간 이내로 임박")
        elif hours <= 24:
            reasons.append("오늘 안에 마감되는 작업")

    if not reasons:
        reasons.append("다른 일정과 충돌하지 않는 시간에 배정")

    return ", ".join(reasons)


def get_advice(task):
    if task.importance >= 5:
        return "집중력이 높은 시간에 처리하고 알림을 꺼두세요."
    elif task.duration >= 120:
        return "중간에 5~10분 휴식을 취해 집중력을 유지하세요."
    elif task.duration <= 30:
        return "짧은 작업을 한 번에 끝내고 완료 표시를 하세요."
    return "작업 목표를 구체적으로 정하고 완료 후 다음 일정으로 이동하세요."


def overlaps(start, end, event):
    return start < event.end and end > event.start


def find_slot(task, day_start, day_end, events, buffer_min=10):
    """
    기존 일정과 겹치지 않는 가장 이른 시간대를 찾는다.
    작업 후에는 기본 10분의 전환 시간을 확보한다.
    """
    cursor = day_start
    occupied = sorted(events, key=lambda e: e.start)

    for event in occupied:
        if cursor >= day_end:
            return None

        candidate_end = cursor + timedelta(minutes=task.duration)

        if candidate_end <= event.start:
            return cursor, candidate_end

        if cursor < event.end:
            cursor = event.end

    candidate_end = cursor + timedelta(minutes=task.duration)

    if candidate_end <= day_end:
        return cursor, candidate_end

    return None


def build_schedule(day_start, day_end, tasks, fixed_events):
    now = day_start
    events = list(fixed_events)
    scheduled = []
    unscheduled = []

    # 중요도와 마감 시간을 기준으로 우선순위를 계산한다.
    tasks.sort(
        key=lambda t: get_priority(t, now, day_end),
        reverse=True
    )

    for task in tasks:
        slot = find_slot(
            task, day_start, day_end, events
        )

        if slot is None:
            unscheduled.append(task)
            continue

        start, end = slot

        new_event = Event(
            task.name, start, end, "할 일"
        )
        events.append(new_event)
        events.sort(key=lambda e: e.start)

        scheduled.append({
            "task": task,
            "start": start,
            "end": end,
            "reason": get_reason(task, now),
            "advice": get_advice(task),
        })

    return sorted(
        scheduled, key=lambda item: item["start"]
    ), events, unscheduled


def print_schedule(day_start, day_end, scheduled,
                   fixed_events, unscheduled):
    print("\n" + "=" * 60)
    print("          AI 맞춤형 시간 관리 결과")
    print("=" * 60)

    all_events = list(fixed_events)

    for item in scheduled:
        all_events.append(Event(
            item["task"].name,
            item["start"],
            item["end"],
            "할 일"
        ))

    all_events.sort(key=lambda e: e.start)

    cursor = day_start
    free_minutes = 0

    for event in all_events:
        if event.start > cursor:
            gap = int((event.start - cursor).total_seconds() / 60)
            free_minutes += gap

            print(
                f"\n[여유 시간] {cursor:%H:%M} ~ "
                f"{event.start:%H:%M} ({gap}분)"
            )

            if gap >= 30:
                print("  조언: 휴식이나 예상치 못한 일에 활용하세요.")
            else:
                print("  조언: 다음 일정 준비에 활용하세요.")

        print(
            f"\n[{event.kind}] {event.start:%H:%M} ~ "
            f"{event.end:%H:%M} | {event.name}"
        )

        if event.kind == "고정 일정":
            print("  이유: 이미 확정된 일정입니다.")

        cursor = max(cursor, event.end)

    if cursor < day_end:
        gap = int((day_end - cursor).total_seconds() / 60)
        free_minutes += gap
        print(
            f"\n[여유 시간] {cursor:%H:%M} ~ "
            f"{day_end:%H:%M} ({gap}분)"
        )
        print("  조언: 남은 시간은 휴식 또는 예비 시간으로 남겨두세요.")

    total_minutes = int(
        (day_end - day_start).total_seconds() / 60
    )
    busy_minutes = total_minutes - free_minutes

    print("\n" + "-" * 60)
    print(f"전체 사용 가능 시간: {total_minutes}분")
    print(f"배정된 일정 및 작업: {busy_minutes}분")
    print(f"확보된 여유 시간: {free_minutes}분")
    print(
        f"여유 시간 비율: "
        f"{free_minutes / total_minutes * 100:.1f}%"
        if total_minutes > 0 else "여유 시간 비율: 계산 불가"
    )

    if unscheduled:
        print("\n[배정하지 못한 작업]")
        for task in unscheduled:
            print(
                f"- {task.name} ({task.duration}분, "
                f"중요도 {task.importance}/5)"
            )
        print("조언: 사용 시간을 늘리거나 작업을 나누고,")
        print("      중요도가 낮은 작업의 일정을 조정하세요.")

    print("=" * 60)


def main():
    print("AI 시간 관리 시스템을 시작합니다.")

    day = input("날짜 (YYYY-MM-DD): ").strip()
    start_text = input("하루 시작 시간 (HH:MM): ").strip()
    end_text = input("하루 종료 시간 (HH:MM): ").strip()

    day_start = parse_time(day, start_text)
    day_end = parse_time(day, end_text)

    if day_end <= day_start:
        print("오류: 종료 시간은 시작 시간보다 늦어야 합니다.")
        return

    tasks = []
    fixed_events = []

    task_count = int(input("처리할 작업 수: "))

    for i in range(task_count):
        print(f"\n작업 {i + 1}")
        name = input("작업 이름: ").strip()
        duration = int(input("예상 소요 시간(분): "))
        importance = int(input("중요도(1~5): "))

        deadline_text = input(
            "마감 시간 (HH:MM, 없으면 Enter): "
        ).strip()

        deadline = (
            parse_time(day, deadline_text)
            if deadline_text else None
        )

        if duration <= 0 or not 1 <= importance <= 5:
            print("잘못된 입력입니다. 이 작업은 건너뜁니다.")
            continue

        tasks.append(Task(
            name, duration, importance, deadline
        ))

    fixed_count = int(input("\n고정 일정 수: "))

    for i in range(fixed_count):
        print(f"\n고정 일정 {i + 1}")
        name = input("일정 이름: ").strip()
        start = parse_time(
            day, input("시작 시간 (HH:MM): ").strip()
        )
        end = parse_time(
            day, input("종료 시간 (HH:MM): ").strip()
        )

        if start >= end or start < day_start or end > day_end:
            print("시간 범위가 잘못되어 이 일정을 건너뜁니다.")
            continue

        if any(overlaps(start, end, event)
               for event in fixed_events):
            print("기존 고정 일정과 겹쳐 이 일정을 건너뜁니다.")
            continue

        fixed_events.append(Event(
            name, start, end, "고정 일정"
        ))

    # 작업은 현재 고정 일정과 겹치지 않는 시간에 배정한다.
    scheduled, _, unscheduled = build_schedule(
        day_start, day_end, tasks, fixed_events
    )

    print_schedule(
        day_start, day_end, scheduled,
        fixed_events, unscheduled
    )


if __name__ == "__main__":
    main()

