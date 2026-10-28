; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x35 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))))))
(let ((?x65 ((_ extract 15 0) ?x35)))
(let (($x80 (and (distinct (ite (bvsgt (_ bv0 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let (($x18 (and (distinct (ite (= (ite (bvsgt (_ bv65529 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite (and (and (distinct (ite (bvsgt (_ bv8 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x18) (_ bv1 1) (_ bv0 1))))
(let (($x21 (and (distinct ?x20 (_ bv0 1)) true)))
(and (distinct (ite $x21 (ite $x80 (bvneg ((_ extract 15 0) a)) a) c) (ite $x21 (ite $x80 ((_ extract 15 0) (bvneg ?x65)) ?x65) c)) true))))))))
(check-sat)
